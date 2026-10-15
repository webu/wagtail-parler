# Future imports
from __future__ import annotations

from typing import TYPE_CHECKING

from modelcluster.models import get_serializable_data_for_fields
from modelcluster.models import model_from_serializable_data
from parler.cache import IsMissing
from parler.models import TranslatableModel

if TYPE_CHECKING:
    from typing import Dict
    from typing import Tuple

    from django.db.models import Manager


class ToDelete(IsMissing):
    pass


TO_DELETE = ToDelete()


def is_cluster_manager(rel: "Manager") -> bool:
    """
    Unfortunately, ModelCluster DeferringRelatedManager can not be imported, it is
    generated dynamically. So we test if we had a specific method from this manager
    """
    return hasattr(rel, "_get_cluster_related_objects")


class WagtailParlerModel(TranslatableModel):
    class Meta:
        abstract = True

    def serializable_data(self) -> dict:
        try:
            data = super().serializable_data()
        except AttributeError:
            data = get_serializable_data_for_fields(self)

        if is_cluster_manager(getattr(self, self._parler_meta.root_rel_name)):
            # If yes, we do not need to do anything, ModelCluster should already
            # have serialize our translations, thanks to ParentalKey on master ;-)
            pass
        else:
            # Else, let's do some magic (and later some black magic when rebuilding from data)
            data.update(self._serializable_translated_data())
        return data

    @classmethod
    def from_serializable_data(
        cls, data: dict, check_fks: bool = True, strict_fks: bool = False
    ) -> TranslatableModel:
        if not hasattr(cls._parler_meta.root_model, "from_serializable_data"):
            translations = data.pop(cls._parler_meta.root_rel_name, [])
        try:
            instance = super().from_serializable_data(data, check_fks, strict_fks)
        except AttributeError:
            instance = model_from_serializable_data(
                cls, data, check_fks=check_fks, strict_fks=strict_fks
            )
        if not hasattr(cls._parler_meta.root_model, "from_serializable_data"):
            data[cls._parler_meta.root_rel_name] = translations
        cls._from_serializable_translated_data(
            instance, data, check_fks=check_fks, strict_fks=strict_fks
        )
        return instance

    @classmethod
    def _from_serializable_translated_data(
        cls, instance: TranslatableModel, data: dict, check_fks: bool, strict_fks: bool
    ) -> None:
        i18n_meta = instance._parler_meta.root
        i18n_model = i18n_meta.model
        locale_cache = instance._translations_cache[i18n_model]
        empty_locales = []
        old_translations = data.get(instance._parler_meta.root_rel_name, [])
        if isinstance(old_translations, list):
            old_translations = {trans["language_code"]: trans for trans in old_translations}
        current_translations = {}
        for locale in instance.get_available_languages(include_unsaved=True):
            current_translations[locale] = instance.get_translation(locale)
            if locale not in old_translations:
                locale_cache[locale] = TO_DELETE
        for locale, trans_data in old_translations.items():
            locale_cache.pop(locale, None)
            if not trans_data or all(not d for d in data.values()):
                empty_locales.append(locale)
            else:
                translated_instances = instance._set_translated_fields(**trans_data)
                for ti in translated_instances:
                    instance._translations_cache[ti.__class__][locale] = ti
        original_state = instance._state.adding
        instance._state.adding = True

        # Hack to avoid fetching from DB in case we empty a translation
        for locale in empty_locales:
            # now, parler will believe there are no translations for this local and will use
            # fallbacks if available
            locale_cache[locale] = instance._get_translated_model(locale, use_fallback=True)
        if is_cluster_manager(getattr(instance, instance._parler_meta.root_rel_name)):
            # MAJ du mod-le cluster avec ce qu'on a réellement
            instance.translations.clear()
            for locale, translation in locale_cache.items():
                if translation is not TO_DELETE:
                    instance.translations.add(translation)

        instance._state.adding = original_state

    def _serializable_translated_data(self) -> dict:
        translations = []
        i18n_meta = self._parler_meta.root
        i18n_model = i18n_meta.model
        for locale in (
            set(self.get_available_languages()) | self._translations_cache[i18n_model].keys()
        ):
            try:
                translation = self._get_translated_model(
                    locale, use_fallback=False, auto_create=False
                )
            except i18n_model.DoesNotExist:
                continue

            if hasattr(translation, "serializable_data") and callable(
                translation.serializable_data
            ):
                trans_data = translation.serializable_data()
            else:
                trans_data = get_serializable_data_for_fields(translation)
            translations.append(trans_data)
        return {
            self._parler_meta.root_rel_name: translations,
        }

    def save(self, *args: Tuple, **kwargs: Dict) -> None:
        """
        Fix bug of django-parler: it removes update_fields but when saving a revision should only
        save the `latest_revision` field: not the translations !
        """
        update_fields = kwargs.get("update_fields", None)
        self._do_not_save_translations = (
            update_fields and self._parler_meta.root.rel_name not in update_fields
        )
        super().save(*args, **kwargs)
        self._do_not_save_translations = None

    def save_translations(self, *args: Tuple, **kwargs: Dict) -> None:
        if getattr(self, "_do_not_save_translations", False):
            return
        ret = super().save_translations(*args, **kwargs)
        for i18n_model, data in self._translations_cache.items():
            for locale, translation in data.items():
                if isinstance(translation, ToDelete):
                    translation = i18n_model.objects.filter(
                        language_code=locale, master_id=self.pk
                    ).first()
                    if translation:
                        translation.delete()
        return ret
