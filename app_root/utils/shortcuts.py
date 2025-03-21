#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtGui import QShortcut

# KF6 imports
try:
    from PyKF6.KGlobalAccel import KGlobalAccel
    from PyKF6.KGuiAddons import KStandardShortcut
    from PyKF6.KConfigWidgets import KStandardAction
    _has_kde = True
except ImportError:
    _has_kde = False


class GlobalShortcut(QObject):
    """Global shortcut handler that works with KDE and fallbacks for other environments"""
    
    # Signal emitted when the shortcut is triggered
    activated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortcut = None
        self.kde_action = None
        self.shortcut_str = None
    
    def register(self, key_sequence, callback=None):
        """Register a global shortcut"""
        
        # Store the key sequence
        if isinstance(key_sequence, str):
            self.shortcut_str = key_sequence
            key_sequence = QKeySequence(key_sequence)
        else:
            self.shortcut_str = key_sequence.toString()
        
        # Connect callback if provided
        if callback:
            self.activated.connect(callback)
        
        # Use KDE global shortcuts if available
        if _has_kde:
            return self._register_kde(key_sequence)
        else:
            return self._register_fallback(key_sequence)
    
    def _register_kde(self, key_sequence):
        """Register a global shortcut using KDE's global accel"""
        
        # In KF6, we use QAction with KGlobalAccel
        # This implementation is done in main_window.py directly
        # when KF6_AVAILABLE is True
        print("KDE global shortcuts will be handled by KGlobalAccel in main_window.py")
        return True
    
    def _register_fallback(self, key_sequence):
        """Register a fallback shortcut for non-KDE environments"""
        print(f"Using application-level shortcut for '{self.shortcut_str}' (not global)")
        
        # Use QShortcut for application-level shortcuts
        # Note: These aren't truly global, but will work for demo purposes
        try:
            if self.parent():
                self.shortcut = QShortcut(key_sequence, self.parent())
                self.shortcut.activated.connect(self.activated.emit)
                return True
            else:
                print("Warning: No parent widget for shortcut")
                return False
        except Exception as e:
            print(f"Failed to register shortcut: {str(e)}")
            return False
    
    def unregister(self):
        """Unregister the shortcut"""
        if _has_kde and self.kde_action:
            KGlobalAccel.setGlobalShortcut(self.kde_action, QKeySequence())
            self.kde_action = None
            return True
        elif self.shortcut:
            self.shortcut.setEnabled(False)
            self.shortcut.deleteLater()
            self.shortcut = None
            return True
        
        return False