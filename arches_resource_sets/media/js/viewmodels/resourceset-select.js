import $ from "jquery";
import ko from "knockout";
import arches from "arches";
import WidgetViewModel from "viewmodels/widget";

export default function (params) {
    const self = this;
    const nameLookup = ko.observable({});
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

    const extractValue = function (langEntry) {
        if (typeof langEntry === "string") return langEntry;
        if (langEntry && typeof langEntry === "object") return langEntry.value || "";
        return "";
    };

    const getDescriptionText = function (description) {
        if (!description) {
            return "";
        }

        // I18n_TextField may be serialized as a JSON string
        if (typeof description === "string") {
            try {
                description = JSON.parse(description);
            } catch (e) {
                return description;
            }
        }

        if (typeof description !== "object") {
            return String(description);
        }

        const activeLanguage = arches.activeLanguage || "en";

        // 1. Exact match: e.g. "en-US"
        if (description[activeLanguage]) {
            return extractValue(description[activeLanguage]);
        }

        // 2. Language prefix match: e.g. "en" from "en-US"
        const langPrefix = activeLanguage.split("-")[0];
        if (langPrefix !== activeLanguage && description[langPrefix]) {
            return extractValue(description[langPrefix]);
        }

        // 3. Any key that starts with the same prefix: e.g. "en-GB" when active is "en-US"
        const prefixKey = Object.keys(description).find((key) =>
            key.startsWith(langPrefix),
        );
        if (prefixKey) {
            return extractValue(description[prefixKey]);
        }

        // 4. Fall back to the first available language
        const firstKey = Object.keys(description)[0];
        if (firstKey) {
            return extractValue(description[firstKey]);
        }

        return "";
    };

    const getLabel = function (resourceSet) {
        const description = getDescriptionText(resourceSet.description);
        return description || resourceSet.id;
    };

    const setLookupEntries = function (entries) {
        if (!Array.isArray(entries) || !entries.length) {
            return;
        }

        const currentLookup = nameLookup();
        const nextLookup = { ...currentLookup };
        let hasChanges = false;

        entries.forEach((item) => {
            if (item?.id && item?.text && nextLookup[item.id] !== item.text) {
                nextLookup[item.id] = item.text;
                hasChanges = true;
            }
        });

        if (hasChanges) {
            nameLookup(nextLookup);
        }
    };

    const getLookupLabel = function (id) {
        if (!id) {
            return "";
        }
        const lookup = nameLookup();
        return lookup[id] || id;
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
        if (!resourceSetsUrl) {
            return Promise.resolve([]);
        }

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
                    setLookupEntries(entries);
                    return entries;
                })
                .catch((error) => {
                    preloadPromise = null;
                    console.warn("Could not preload resource sets", error);
                    return [];
                });
        }

        return preloadPromise;
    };

    const loadResults = function (term) {
        return preloadResourceSets().then((entries) => filterEntries(entries, term));
    };

    this.getReportLabel = function (id) {
        return getLookupLabel(id);
    };

    this.displayValue = ko.computed(function () {
        const ids = normalizeIds(ko.unwrap(self.value));
        if (!ids.length) {
            return "";
        }

        const labels = ids.map((id) => self.getReportLabel(id)).filter((label) => !!label);
        if (!labels.length) {
            return "";
        }

        return self.multiple ? labels.join(", ") : labels[0];
    });

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
                setLookupEntries(allResourceSets);

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
                setLookupEntries([item]);
            }
            return item.text || item.id;
        },
        templateSelection: function (item) {
            return getLookupLabel(item?.id) || item?.text || item?.id || "";
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