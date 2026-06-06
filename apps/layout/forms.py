from django import forms

from apps.layout.models import CMSPage


class ProjektiPageAdminForm(forms.ModelForm):
    """Pojednostavljena forma — slug i tip su uvek fiksni."""

    class Meta:
        model = CMSPage
        fields = ("title", "is_active")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.page_type = CMSPage.PageType.PROJEKTI
        instance.slug = "projekti"
        if commit:
            instance.save()
        return instance
