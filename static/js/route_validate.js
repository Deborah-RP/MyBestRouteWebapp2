var ValidateIcon = {
    valid: 'fa fa-check-circle fa-fw',
    invalid: 'fa fa-exclamation-circle fa-fw',
    validating: 'fa fa-refresh fa-fw'
}

/*
* fuction to validate forms
*   fields: object contains fields that required validation
*       field_id: name of the field
*           validator_list: list of validators for the field
*               name: name of the validator
*                   valid_params: list of params for validator
*       
*/
$.fn.formValidate = function (fields){
    var $form = this;
    
    var is_required = function(params){
        console.log(params.msg);
    }
    
    var validator_def = {
        required: is_required,   
    }
    
    for (var field_id in fields){
        var validator_list = fields[field_id];
        for (var validator_name in validator_list){
            var validate_func = validator_def[validator_name];
            var params = validator_list[validator_name]
            validate_func(params);
        }
    }
    
}