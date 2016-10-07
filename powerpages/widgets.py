# -*- coding: utf-8 -*-

from django import forms


class SourceCodeEditor(forms.Textarea):
    """Textarea being source code editor"""

    class Media:
        js = ('powerpages/js/ace/ace.js', 'powerpages/js/bind_ace_editor.js')

    HANDLER_CLASS = 'handle-ace-editor'

    def __init__(self, attrs=None):
        super(SourceCodeEditor, self).__init__(attrs)
        # Add handler class to widget's classes
        classes = [
            cls for cls in self.attrs.get('class', '').split(' ') if cls
        ]
        if self.HANDLER_CLASS not in classes:
            classes.insert(0, self.HANDLER_CLASS)
        self.attrs['class'] = ' '.join(classes)
