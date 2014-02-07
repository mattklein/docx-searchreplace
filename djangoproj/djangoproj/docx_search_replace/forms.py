from django import forms


# TODO don't think I need this at all
class UploadArchiveForm(forms.Form):
    file_ = forms.FileField()


class FileChooserForm(forms.Form):
    pass
