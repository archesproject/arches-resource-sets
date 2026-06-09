import $ from "jquery";
import ko from "knockout";
import arches from "arches";
import WidgetViewModel from "viewmodels/widget";

export default function (params) {
    const self = this;
    const nameLookup = {};
    const resourceSetsUrl = arches.urls.resource_sets;
    let preloadedResourceSets = [];
    let preloadPromise = null;

    params.configKeys = ["placeholder", "defaultValue", "multiValue"];
    WidgetViewModel.apply(this, [params]);

    this.multiple = !!ko.unwrap(this.multiValue);
    this.selectionValue = ko.observable([]);

    const normalizeIds = function (value) {
        if (value === null || typeof value === "undefined" || value === "") {
            return [];
        }

        if (Array.isArray(value)) {
            return value
                .map((entry) => {
                    if (entry && typeof entry === "object") {
                        return entry.id || entry.resource_set_id || null;
                    }
                    return entry;
                })
                .filter((entry) => !!entry);
        }

        if (typeof value === "object") {
            return value.id ? [value.id] : [];
        }

        return [value];
    };

    const toStoredValue = function (ids) {
        if (self.multiple) {
            return ids;
        }
        return ids.length ? ids[0] : null;
    };

    const getDescriptionText = function (description) {
        if (!description) {
            return "";
        }
        if (typeof description === "string") {
            return description;
        }
        if (typeof description === "object") {
            const languageValue = description[arches.activeLanguage];
            if (typeof languageValue === "string") {
                return languageValue;
            }
            if (languageValue && typeof languageValue === "object") {
                return languageValue.value || "";
            }
            const fallback = description[Object.keys(description)[0]];
            if (typeof fallback === "string") {
                return fallback;
            }
            if (fallback && typeof fallback === "object") {
                return fallback.value || "";
            }
        }
        return "";
    };

    const getLabel = function (resourceSet) {
        const description = getDescriptionText(resourceSet.description);
        return description || resourceSet.id;
    };

    const filterEntries = function (entries, term) {
        const normalizedTerm = (term || "").toLowerCase();
        return entries.filter((entry) => {
            if (!normalizedTerm) {
                return true;
            }
            return (
                String(entry.text).toLowerCase().includes(normalizedTerm) ||
                String(entry.id).toLowerCase().includes(normalizedTerm)
            );
        });
    };

    const fetchAllResourceSets = function () {
        console.log("resourceSetsUrl: ", resourceSetsUrl);
        return window
            .fetch(resourceSetsUrl, { credentials: "include" })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Could not fetch resource sets");
                }
                return response.json();
            })
            .then((payload) => {
                const resourceSets = payload.resource_sets || [];
                return resourceSets.map((resourceSet) => ({
                    id: resourceSet.id,
                    text: getLabel(resourceSet),
                }));
            });
    };

    const preloadResourceSets = function () {
        if (!preloadPromise) {
            preloadPromise = fetchAllResourceSets()
                .then((entries) => {
                    preloadedResourceSets = entries;
                    entries.forEach((item) => {
                        nameLookup[item.id] = item.text;
                    });
                    return entries;
                })
                .catch((error) => {
                    preloadPromise = null;
                    throw error;
                });
        }

        return preloadPromise;
    };

    const loadResults = function (term) {
        return preloadResourceSets().then((entries) => filterEntries(entries, term));
    };

    const syncSelectionFromValue = function (value) {
        const ids = normalizeIds(ko.unwrap(value));
        if (JSON.stringify(self.selectionValue()) !== JSON.stringify(ids)) {
            self.selectionValue(ids);
        }
    };

    this.selectionValue.subscribe((selection) => {
        const normalized = Array.isArray(selection)
            ? selection.filter((entry) => !!entry)
            : selection
              ? [selection]
              : [];

        self.value(toStoredValue(normalized));
    });

    this.value.subscribe(syncSelectionFromValue);
    syncSelectionFromValue(this.value());

    this.select2Config = {
        value: self.selectionValue,
        minimumInputLength: 0,
        clickBubble: true,
        multiple: this.multiple,
        closeOnSelect: true,
        placeholder: self.placeholder,
        allowClear: true,
        ajax: {
            url: resourceSetsUrl,
            dataType: "json",
            quietMillis: 250,
            data: function (requestParams) {
                return {
                    term: requestParams.term || "",
                };
            },
            processResults: function (data, requestParams) {
                const term = requestParams?.term || "";
                let allResourceSets = [];

                if (Array.isArray(data?.resource_sets)) {
                    allResourceSets = data.resource_sets.map((resourceSet) => ({
                        id: resourceSet.id,
                        text: getLabel(resourceSet),
                    }));
                    preloadedResourceSets = allResourceSets;
                } else if (preloadedResourceSets.length) {
                    allResourceSets = preloadedResourceSets;
                }

                allResourceSets = filterEntries(allResourceSets, term);
                allResourceSets.forEach((item) => {
                    nameLookup[item.id] = item.text;
                });

                return {
                    results: allResourceSets,
                    pagination: { more: false },
                };
            },
        },
        templateResult: function (item) {
            if (item.loading) {
                return item.text;
            }
            if (item.id && item.text) {
                nameLookup[item.id] = item.text;
            }
            return item.text || item.id;
        },
        templateSelection: function (item) {
            return nameLookup[item.id] || item.text || item.id || "";
        },
        escapeMarkup: function (markup) {
            return markup;
        },
        initSelection: function (el, callback) {
            const selectedIds = normalizeIds(ko.unwrap(self.value));
            if (!selectedIds.length) {
                callback([]);
                return;
            }

            loadResults("").then((results) => {
                const selectedItems = results.filter((item) =>
                    selectedIds.includes(item.id),
                );

                selectedItems.forEach((item) => {
                    const option = new Option(item.text, item.id, true, true);
                    $(el).append(option);
                });

                callback(selectedItems);
            });
        },
    };

    // Preload options from ResourceSet table once so the dropdown has data immediately.
    preloadResourceSets();
}