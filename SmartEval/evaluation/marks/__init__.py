from .factory import build_marks_calculator
from .marks_calculator import MarksCalculator, WeightedMarksCalculator
from .total_marks_calculator import TotalMarksCalculator

__all__ = ["MarksCalculator", "TotalMarksCalculator", "WeightedMarksCalculator", "build_marks_calculator"]
