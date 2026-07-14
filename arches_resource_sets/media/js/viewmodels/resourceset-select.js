import $ from "jquery";
import ko from "knockout";
import arches from "arches";
import WidgetViewModel from "viewmodels/widget";

export default function (params) {
    const NAME_LOOKUP = ko.observable({});
    const self = this;

    let cachedResourceSets = [];

    params.configKeys = ["placeholder", "defaultValue", "multiValue"];
    WidgetViewModel.apply(this, [params]);

    this.multiple = !!ko.unwrap(this.multiValue);

    const normalizeIds = (value) => {
        if (!value) {
            return [];
        }
        return Array.isArray(value) ? value : [value];
    };

    const toEntries = (data) => {
        const resourceSets = data?.resource_sets || [];
        return resourceSets.map((resourceSet) => ({
            id: resourceSet.id,
            text: resourceSet.description || resourceSet.id,
        }));
    };

    this.getLookupLabel = (id) => NAME_LOOKUP()[id] || id;

    const loadResourceSets = () => {
        return $.ajax({
            url: arches.urls.resource_sets,
            dataType: "json",
        })
            .then((data) => {
                cachedResourceSets = toEntries(data);
                NAME_LOOKUP(
                    Object.fromEntries(
                        cachedResourceSets.map((e) => [e.id, e.text]),
                    ),
                );
                return cachedResourceSets;
            })
            .fail((error) => {
                console.warn("Could not load resource sets", error);
                return [];
            });
    };

    loadResourceSets();

    const filterEntries = (entries, term) => {
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

    this.displayValue = ko.computed(() =>
        normalizeIds(ko.unwrap(self.value))
            .map((id) => self.getLookupLabel(id))
            .filter((label) => !!label)
            .join(", "),
    );

    this.selectionValue = ko.pureComputed({
        read: () => normalizeIds(self.value()),
        write: (selection) => self.value(normalizeIds(selection)),
    });

    this.select2Config = {
        value: self.selectionValue,
        minimumInputLength: 0,
        clickBubble: true,
        multiple: this.multiple,
        closeOnSelect: true,
        placeholder: self.placeholder,
        allowClear: true,
        ajax: {
            url: arches.urls.resource_sets,
            dataType: "json",
            quietMillis: 250,
            data: (requestParams) => ({ term: requestParams.term || "" }),
            processResults: (data, requestParams) => {
                const term = requestParams?.term || "";
                cachedResourceSets = toEntries(data);

                return {
                    results: filterEntries(cachedResourceSets, term),
                    pagination: { more: false },
                };
            },
        },
        templateSelection: (item) =>
            self.getLookupLabel(item?.id) || item?.text || item?.id || "",
        initComplete: false,
        initSelection: (el, callback) => {
            const selectedIds = normalizeIds(ko.unwrap(self.value));
            if (!selectedIds.length) {
                callback([]);
                return;
            }

            const setSelectionData = (entries) => {
                const selectedItems = entries.filter((item) =>
                    selectedIds.includes(item.id),
                );

                if (!self.select2Config.initComplete) {
                    selectedItems.forEach((item) => {
                        const option = new Option(item.text, item.id, true, true);
                        $(el).append(option);
                    });
                    self.select2Config.initComplete = true;
                }

                callback(selectedItems);
            };

            if (cachedResourceSets.length) {
                setSelectionData(cachedResourceSets);
            } else {
                loadResourceSets().then((entries) => {
                    if (entries.length) {
                        setSelectionData(entries);
                    } else {
                        callback([]);
                    }
                });
            }
        },
    };
    this.select2ConfigMulti = { ...this.select2Config };
    this.select2ConfigMulti.multiple = true;
}