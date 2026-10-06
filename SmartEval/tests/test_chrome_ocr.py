from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import fitz
from config.settings import Settings
from integration.chrome_ocr_service import ChromeOCRService
from integration.ocr_factory import create_ocr_service
from integration.ocr_service import OCRResult
from integration.smarthtr_preprocessor import PreprocessedChromeOCRService
from integration.student_text_provider import SmartHTRIntegrationService, SmartHTRStudentTextProvider
from services.input_manager import InputManager
from app.input_pipeline import InputPipeline
from integration.chrome_window import ChromeWindowTracker


class ChromeWindowTests(unittest.TestCase):
    def tracker(self, current, foreground=2):
        tracker = ChromeWindowTracker.__new__(ChromeWindowTracker)
        tracker.user32 = Mock()
        tracker.user32.GetForegroundWindow.return_value = foreground
        tracker.before = {1: (10, 'Existing - Google Chrome')}
        tracker.target = None
        tracker.windows = Mock(return_value=current)
        return tracker

    def test_closes_only_new_window_even_after_focus_changes(self):
        tracker = self.tracker({1: (10, 'Existing - Google Chrome'), 2: (10, 'PDF - Google Chrome')})
        tracker.capture()
        tracker.user32.GetForegroundWindow.return_value = 1
        self.assertTrue(tracker.close())
        tracker.user32.PostMessageW.assert_called_once_with(2, 0x0010, 0, 0)

    def test_existing_or_ambiguous_windows_are_not_closed(self):
        for current in ({1: (10, 'Existing - Google Chrome')},
                        {2: (10, 'PDF - Google Chrome'), 3: (10, 'Other - Google Chrome')}):
            tracker = self.tracker(current)
            tracker.capture()
            self.assertFalse(tracker.close())
            tracker.user32.PostMessageW.assert_not_called()

    def test_changed_window_identity_is_not_closed(self):
        tracker = self.tracker({2: (10, 'PDF - Google Chrome')})
        tracker.capture()
        tracker.windows.return_value = {2: (10, 'Different tab - Google Chrome')}
        self.assertFalse(tracker.close())
        tracker.user32.PostMessageW.assert_not_called()


class ChromeOCRTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pdf = Path(self.temp.name) / 'processed with spaces.pdf'
        with fitz.open() as doc:
            doc.new_page()
            doc.save(self.pdf)
        self.settings = Settings(log_directory=Path(self.temp.name), chrome_ocr_initial_wait_seconds=0,
                                 chrome_ocr_retry_delay_seconds=0, chrome_ocr_stable_attempts=2)
        self.gui = Mock()
        self.clipboard = Mock()

    def run_copies(self, values, launch_error=None):
        self.clipboard.paste.side_effect = ['original clipboard', *values]
        with patch('integration.chrome_ocr_service.import_module', side_effect=[self.clipboard, self.gui]), \
             patch.object(ChromeOCRService, 'executable', return_value=Path('chrome.exe').resolve()), \
             patch('integration.chrome_ocr_service.subprocess.Popen', side_effect=launch_error) as launch, \
             patch('integration.chrome_ocr_service.time.sleep'), \
             patch('integration.chrome_ocr_service.ChromeWindowTracker') as tracker:
            result = ChromeOCRService(self.settings).recognize(self.pdf)
        if tracker.called:
            tracker.return_value.close.assert_called_once()
        self.clipboard.copy.assert_called_with('original clipboard')
        self.assertTrue(result.metadata['clipboard_restored'])
        return result, launch

    def test_progressive_copy_stabilizes_and_launches_only_normal_chrome(self):
        best = 'Q1. ' + 'a' * 80 + '\r\n'
        result, launch = self.run_copies(['a' * 30, best, best])
        self.assertTrue(result.success)
        self.assertEqual(result.metadata['attempt_character_counts'], [30, len(best), len(best)])
        self.assertEqual(result.extracted_text, best.strip())
        self.assertEqual(launch.call_args.args[0], [str(Path('chrome.exe').resolve()), '--new-window', self.pdf.as_uri()])
        sentinels = [c.args[0] for c in self.clipboard.copy.call_args_list[:-1]]
        self.assertEqual(len(set(sentinels)), 3)

    def test_longest_is_retained_when_later_copies_shrink(self):
        result, _ = self.run_copies(['x' * 100, 'x' * 30, 'x' * 30, '', 'x' * 30])
        self.assertEqual(result.extracted_text, 'x' * 100)
        self.assertEqual(len(result.metadata['attempt_character_counts']), 5)

    def test_launch_failure_restores_clipboard(self):
        result, _ = self.run_copies([], OSError('launch denied'))
        self.assertFalse(result.success)
        self.assertIn('failed to launch', result.error)

    def test_empty_and_short_results_fail(self):
        for value, error in [('', 'empty'), ('abc', 'threshold')]:
            result, _ = self.run_copies([value] * 5)
            self.assertFalse(result.success)
            self.assertIn(error, result.error)

    def test_unchanged_sentinel_is_never_returned(self):
        state = ['original clipboard']
        self.clipboard.copy.side_effect = lambda value: state.__setitem__(0, value)
        self.clipboard.paste.side_effect = lambda: state[0]
        with patch('integration.chrome_ocr_service.import_module', side_effect=[self.clipboard, self.gui]), \
             patch.object(ChromeOCRService, 'executable', return_value=Path('chrome.exe')), \
             patch('integration.chrome_ocr_service.subprocess.Popen'), \
             patch('integration.chrome_ocr_service.time.sleep'), \
             patch('integration.chrome_ocr_service.ChromeWindowTracker') as tracker:
            result = ChromeOCRService(self.settings).recognize(self.pdf)
        if tracker.called:
            tracker.return_value.close.assert_called_once()
        self.assertIn('clipboard never changed', result.error)
        self.assertEqual(result.extracted_text, '')
        self.assertEqual(state[0], 'original clipboard')

    def test_missing_pdf_restores_clipboard(self):
        self.pdf.unlink()
        result, _ = self.run_copies([])
        self.assertIn('Processed PDF missing', result.error)

    def test_missing_executable_is_clear(self):
        service = ChromeOCRService(replace(self.settings, chrome_ocr_executable=str(self.pdf.parent / 'missing.exe')))
        with self.assertRaisesRegex(RuntimeError, 'executable missing'):
            service.executable()

    def test_copy_exception_restores_clipboard(self):
        self.gui.hotkey.side_effect = RuntimeError('copy failed')
        result, _ = self.run_copies([])
        self.assertFalse(result.success)
        self.assertIn('copy failed', result.error)

    def test_missing_gui_dependency_restores_clipboard(self):
        self.clipboard.paste.return_value = 'original clipboard'
        with patch('integration.chrome_ocr_service.import_module', side_effect=[self.clipboard, ImportError()]):
            result = ChromeOCRService(self.settings).recognize(self.pdf)
        self.assertIn('pyautogui unavailable', result.error)
        self.clipboard.copy.assert_called_once_with('original clipboard')

    def test_missing_clipboard_dependency_is_clear(self):
        with patch('integration.chrome_ocr_service.import_module', side_effect=ImportError()):
            result = ChromeOCRService(self.settings).recognize(self.pdf)
        self.assertIn('pyperclip unavailable', result.error)

    def test_factory_preprocesses_once_and_exact_text_reaches_parser(self):
        service = create_ocr_service(replace(self.settings, ocr_provider='chrome', output_directory=Path(self.temp.name)))
        self.assertIsInstance(service, PreprocessedChromeOCRService)
        self.assertFalse(service.preprocessor.enforce_upload_limit)
        service.preprocessor = Mock()
        service.preprocessor.preprocess.return_value = self.pdf
        result = OCRResult(provider='chrome', extracted_text='Q1. Exact student answer\nsecond line')
        service.delegate = Mock()
        service.delegate.recognize.return_value = result
        manager = InputManager(student_provider=SmartHTRStudentTextProvider(SmartHTRIntegrationService(service)))
        manager.load_teacher_inputs = Mock(return_value=('questions', 'models'))
        student_parser = Mock()
        student_parser.parse.return_value = []
        pipeline = InputPipeline(self.settings, input_manager=manager, student_parser=student_parser,
                                 question_parser=Mock(), model_parser=Mock(), mapper=Mock())
        pipeline.question_parser.parse.return_value = []
        pipeline.run(Path('questions'), Path('models'), self.pdf)
        service.preprocessor.preprocess.assert_called_once()
        service.delegate.recognize.assert_called_once_with(self.pdf)
        student_parser.parse.assert_called_once_with(result.extracted_text, expected_question_ids=[])


if __name__ == '__main__':
    unittest.main()
