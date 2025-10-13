from modelcluster.models import get_serializable_data_for_fields
from modelcluster.models import model_from_serializable_data
from parler.models import TranslatableModel


class WagtailParlerModel(TranslatableModel):
    class Meta:
        abstract = True

    def serializable_data(self) -> dict:
        try:
            data = super().serializable_data()
        except AttributeError:
            data = get_serializable_data_for_fields(self)
        data.update(self._serializable_translated_data())
        return data

    @classmethod
    def from_serializable_data(
        cls, data: dict, check_fks: bool = True, strict_fks: bool = False
    ) -> TranslatableModel:
        try:
            instance = super().from_serializable_data(data, check_fks, strict_fks)
        except AttributeError:
            instance = model_from_serializable_data(
                cls, data, check_fks=check_fks, strict_fks=strict_fks
            )
        cls._from_serializable_translated_data(
            instance, data, check_fks=check_fks, strict_fks=strict_fks
        )
        return instance

    @classmethod
    def _from_serializable_translated_data(
        cls, instance: TranslatableModel, data: dict, check_fks: bool, strict_fks: bool
    ) -> None:
        if not hasattr(instance, "_parler_meta"):
            return
        i18n_meta = instance._parler_meta.root
        i18n_model = i18n_meta.model
        locale_cache = instance._translations_cache[i18n_model]

        current_translations = {}
        for locale in instance.get_available_languages(include_unsaved=False):
            current_translations[locale] = instance.get_translation(locale)

        old_translations = data.get(instance._parler_meta.root_rel_name, {})
        empty_locales = []
        for locale, trans_data in old_translations.items():
            locale_cache.pop(locale, None)
            if not trans_data or all(not d for d in data.values()):
                empty_locales.append(locale)
            else:
                instance._set_translated_fields(**trans_data)
        original_state = instance._state.adding
        instance._state.adding = True
        # Hack to avoid fetching from DB in case we empty a translation
        for locale in empty_locales:
            # now, parler will believe there are no translations for this local and will use
            # fallbacks if available
            locale_cache[locale] = instance._get_translated_model(locale, use_fallback=True)
        instance._state.adding = original_state

    def _serializable_translated_data(self) -> dict:
        if not hasattr(self, "_parler_meta"):
            return {}

        translations = {}
        for locale in self.get_available_languages(include_unsaved=False):
            translation = self.get_translation(locale)
            if hasattr(translation, "serializable_data") and callable(
                translation.serializable_data
            ):
                trans_data = translation.serializable_data()
            else:
                trans_data = get_serializable_data_for_fields(translation)
            translations[locale] = trans_data
        return {
            self._parler_meta.root_rel_name: translations,
        }
