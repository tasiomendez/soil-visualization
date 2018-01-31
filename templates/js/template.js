// Add model parameters that can be edited prior to a model run
var initGUI = function(model_params) {

    var onSubmitCallback = function(param_name, value) {
        // SEND SOCKET REQUEST
    };

    var addBooleanInput = function(name, value) {
        var checked = (value) ? 'checked' : 'value';

        var wrapper     = $('<div>').attr('class', 'col-sm-6').height('110px');
        var input_group = $('<div>').attr('class', 'input-group').appendTo(wrapper);
        var label       = $('<label>').attr('for', name).attr('class', 'checkbox').appendTo(input_group);
        var input       = $('<input>') .attr('class', 'form-check-input').attr('id', name).attr('type', 'checkbox').attr(checked, checked).appendTo(label);

        input.after(name);
        $('#wrapper-settings').append(wrapper);
    };

    var addSliderInput = function(name, value) {

        var wrapper = $('<div>').attr('class', 'col-sm-6').height('110px');
        var label   = $('<div>').width('100%').text(name).css('text-align', 'center').css('font-weight', 'bolder').appendTo(wrapper);
        var input   = $('<input>').attr('id', name).attr('type', 'text').attr('data-slider-min', '0.001').attr('data-slider-max', '1').attr('data-slider-step', '0.001').attr('data-slider-value', value).attr('data-slider-tooltip', 'hide').css('padding', '0 10px').appendTo(wrapper);
        
        var span          = $('<div>').attr('id', name + '_value').text('Current value: ').width('100%').css('padding-top', '10px').appendTo(wrapper);
        var current_value = $('<span>').attr('id', name + '_number').text(value).appendTo(span);

        var button_group  = $('<div>').attr('class', 'btn-group').attr('role', 'group').css('position', 'absolute').css('right', '15px').appendTo(span);
        var button_down   = $('<button>').attr('type', 'button').attr('class', 'btn btn-default btn-default-down').appendTo(button_group);
        var button_up     = $('<button>').attr('type', 'button').attr('class', 'btn btn-default btn-default-down').appendTo(button_group);

        $('<span>').attr('class', 'glyphicon glyphicon-chevron-down').attr('aria-hidden', 'true').appendTo(button_down);
        $('<span>').attr('class', 'glyphicon glyphicon-chevron-up').attr('aria-hidden', 'true').appendTo(button_up);

        $('#wrapper-settings').append(wrapper);
        input.slider().on('change', function(slideEvt) {
            current_value.text(slideEvt.value.newValue);
        });
        button_down.click(function() {
            input.slider('setValue', input.slider('getValue') - 0.001);
            current_value.text(input.slider('getValue'));
        });
        button_up.click(function() {
            input.slider('setValue', input.slider('getValue') + 0.001);
            current_value.text(input.slider('getValue'));
        })
    };

    var addTextBox = function(param, obj) {
        var well = $('<div class="well">' + obj.value + '</div>')[0];
        sidebar.append(well);
    };

    for (var option in model_params) {

        var type = typeof(model_params[option]);
        var param_str = String(option);

        switch (model_params[option]['type']) {
            case "boolean":
                addBooleanInput(model_params[option]['label'], model_params[option]['value']);
                break;
            case "number":
                addSliderInput(model_params[option]['label'], model_params[option]['value']);
                break;
            case "object":
                addParamInput(param_str, model_params[option]);    // catch-all for params that use Option class
                break;
        }
    }
};