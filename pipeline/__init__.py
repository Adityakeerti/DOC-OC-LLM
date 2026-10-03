"""
pipeline/ — Core extraction modules for DOC-OC v6.

Three simple modules:
    preprocess  →  load image, fix orientation, resize
    extract     →  send to VLM, get JSON
    validate    →  type-check and sanity-check the output
"""

from .preprocess import prepare
from .extract import extract
from .validate import validate, Marksheet
