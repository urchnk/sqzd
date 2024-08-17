from apps.texts.models import Text
from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions


@register(Text)
class DestinationPageTranslationOption(TranslationOptions):
    fields = ("text",)
