import ko from "knockout";
import WidgetViewModel from "viewmodels/widget";

export default function (params) {
    const self = this;
    params.configKeys = ["placeholder", "rows", "defaultValue"];

    WidgetViewModel.apply(this, [params]);

    this.parseError = ko.observable("");
    this.defaultValueParseError = ko.observable("");
    this.textValue = ko.observable("");
    this.defaultValueText = ko.observable("");
    this._updatingFromText = false;

    this.formatValue = function (value) {
        if (value === null || typeof value === "undefined") {
            return "";
        }

        if (typeof value === "string") {
            return value;
        }

        try {
            return JSON.stringify(ko.toJS(value), null, 2);
        } catch (error) {
            return "";
        }
    };

    this.syncFromValue = function (value) {
        if (self._updatingFromText) {
            return;
        }
        self.textValue(self.formatValue(value));
        self.parseError("");
    };

    this.syncFromText = function (text) {
        const trimmed = (text || "").trim();

        if (trimmed === "") {
            self.parseError("");
            self._updatingFromText = true;
            self.value(null);
            self._updatingFromText = false;
            return;
        }

        try {
            const parsed = JSON.parse(trimmed);
            self.parseError("");
            self._updatingFromText = true;
            self.value(parsed);
            self._updatingFromText = false;
        } catch (error) {
            self.parseError(error.message || "Invalid JSON");
        }
    };

    this.syncFromValue(this.value());
    this.value.subscribe(this.syncFromValue);
    this.textValue.subscribe(this.syncFromText);

    this.defaultValueText(this.formatValue(ko.unwrap(this.defaultValue)));

    if (ko.isObservable(this.defaultValue)) {
        this.defaultValue.subscribe((newDefaultValue) => {
            self.defaultValueText(self.formatValue(ko.unwrap(newDefaultValue)));
            self.defaultValueParseError("");
        });
    }

    this.defaultValueText.subscribe((text) => {
        const trimmed = (text || "").trim();

        if (trimmed === "") {
            self.defaultValueParseError("");
            if (ko.isObservable(self.defaultValue)) {
                self.defaultValue(null);
            }
            return;
        }

        try {
            const parsed = JSON.parse(trimmed);
            self.defaultValueParseError("");
            if (ko.isObservable(self.defaultValue)) {
                self.defaultValue(parsed);
            }
        } catch (error) {
            self.defaultValueParseError(error.message || "Invalid JSON");
        }
    });
}