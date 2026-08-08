# SmartEval with SmartHTR

This B.Tech major project automates the evaluation workflow for handwritten university answer sheets.

`SmartHTR/` is an independent handwritten-text-recognition engine. It accepts a complete image or PDF page and exports full page text. It does not compare answers, assign marks, or generate feedback.

`SmartEval/` consumes teacher question papers, teacher model answers, and student text produced by SmartHTR. Its implementation follows this order: input management, question extraction, model-answer extraction, student-answer segmentation, answer mapping, semantic evaluation, deterministic marks, feedback, and final reporting.

The current implementation is SmartHTR baseline OCR plus SmartEval Phase A input management. Model training, semantic scoring, grading, and frontend work are intentionally deferred.
