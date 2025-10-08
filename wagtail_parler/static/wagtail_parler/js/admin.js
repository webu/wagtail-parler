function wagtail_parler_set_current_admin_locale_tab(locale) {
    document.getElementById("wagtail_parler_locale_tab").setAttribute("value", locale);
}

window.addEventListener('DOMContentLoaded', (event) => {
    const store_current_edited_language = (mutationList, observer) => {
        for (const mutation of mutationList) {
            if (mutation.attributeName != "aria-selected") {
                return;
            }
            if (mutation.target.ariaSelected) {
                wagtail_parler_set_current_admin_locale_tab(mutation.target.wagtail_parler_locale);
            }
        }
    };
    const tabs_links = document.querySelectorAll(".w-tabs__tab[id^='tab-label-parler_translations_']");
    let with_parler_tabs = tabs_links.length;
    if (with_parler_tabs) {
        // add an hidden input to know wich tag is currently edited to
        // see the right language version in preview mode
        const form = document.getElementById("w-editor-form");
        const locale_tab_input = document.createElement("input");
        locale_tab_input.setAttribute("name", "wagtail_parler_locale_tab");
        locale_tab_input.setAttribute("type", "hidden");
        locale_tab_input.setAttribute("id", "wagtail_parler_locale_tab");
        form.appendChild(locale_tab_input);
        tabs_links.forEach((target) => {
            if (target.id.startsWith("tab-label-parler_translations_")) {
                with_parler_tabs = true;
                target.wagtail_parler_locale = target.id.replace("tab-label-parler_translations_", "");
                if (target.ariaSelected) {
                    wagtail_parler_set_current_admin_locale_tab(target.wagtail_parler_locale);
                }
                let observer = new MutationObserver(store_current_edited_language);
                observer.observe(target, { attributes: true, childList: false, subtree: false });
            }
        });
    }
});
