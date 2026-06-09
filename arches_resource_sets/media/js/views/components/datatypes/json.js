import ko from "knockout";
import jsonDatatypeTemplate from "templates/views/components/datatypes/json.htm";

const viewModel = function (params) {
    const self = this;
    this.search = params.search;

    if (this.search) {
        const filter = params.filterValue();
        this.node = params.node;
        this.op = ko.observable(filter.op || "~");
        this.searchValue = ko.observable(filter.val || "");
        this.filterValue = ko
            .computed(function () {
                return {
                    op: self.op(),
                    val: self.searchValue(),
                };
            })
            .extend({ throttle: 750 });

        params.filterValue(this.filterValue());
        this.filterValue.subscribe(function (value) {
            params.filterValue(value);
        });
    }
};

export default ko.components.register("json-datatype-config", {
    viewModel: viewModel,
    template: jsonDatatypeTemplate,
});