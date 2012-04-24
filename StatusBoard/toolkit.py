# -*- coding: utf-8 -*-
"""Toolkit."""

import json

class SetEncoder(json.JSONEncoder):
    """PYTHON Y U NO SERIALIZE SETS TO JSON ARRAYS?!"""
    
    def default(self, obj):
        """Make sets JSON-serializable. Kthxbye."""
        if isinstance(obj, set):
            return list(obj)
            
        return json.JSONEncoder.default(self, obj)