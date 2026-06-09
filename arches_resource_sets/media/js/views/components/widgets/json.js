import ko from "knockout";
import JsonWidgetViewModel from "viewmodels/json";
import jsonWidgetTemplate from "templates/views/components/widgets/json.htm";

export default ko.components.register("json-widget", {
    viewModel: JsonWidgetViewModel,
    template: jsonWidgetTemplate,
});