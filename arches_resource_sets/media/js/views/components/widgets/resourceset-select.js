import ko from "knockout";
import ResourceSetSelectViewModel from "viewmodels/resourceset-select";
import resourcesetSelectTemplate from "templates/views/components/widgets/resourceset-select.htm";
import "bindings/select2-query";

export default ko.components.register("resourceset-select-widget", {
    viewModel: ResourceSetSelectViewModel,
    template: resourcesetSelectTemplate,
});