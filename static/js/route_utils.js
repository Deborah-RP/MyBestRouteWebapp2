
//Get the object from the multilevel string key such as "prop1.prop2.prop3"
function get_desc_obj(obj, str_keys){
    var desc_keys = str_keys.split(".");
    while (desc_keys.length && (obj = obj[desc_keys.shift()]));
    return obj;
}

function handleShowItem(e) {
    //console.log("showing " + e.data.show_id);
    $(e.data.show_id).show();
}

function show_item(item_id){
    $(item_id).show();   
}

function hide_item(item_id){
    $(item_id).hide();   
}

function print_obj(obj){
    console.log(JSON.stringify(obj));   
}

//Pad symbol at the beginning of string
function pad_str(old_str, symbol, str_len){
    if (old_str.length < str_len)
        return pad_str(symbol+old_str, symbol, str_len);
    else
        return old_str;
}

/*
* This function will change the css style for objects
* It will accept the below data array[]
*   obj_id: the object that need to change the css style
*   css_array: the array that contains all the css property name and value
*       name: css property name
*       value: css property value
*/

/*function change_css (obj_css_array) {
         sample data
        obj_css_array = [{
			obj_id: pageVar.dnd_id,
			css_array : [{
				name: 'border',
				value: '8px dotted #0B85A1'
				}
			]
		}
		];
    
    if (typeof obj_css_array === "undefined") {
        console.log("undefined obj_css_array in function change_css");
        return false;
    }
    
    $.each(obj_css_array, function(obj_idx, obj) {
        if (obj.css_array === "undefined") {
            console.log("undefined css_array in function change_css");
            return;
        };
        
        var html_obj = $(obj.obj_id);
        //console.log("Changing css for " + obj.obj_id);
        
        $.each(obj.css_array, function(css_idx, css_obj) {
            html_obj.css(css_obj.name, css_obj.value);
        });
    });
    return true;
}*/

//Function to update the progress bar
$.fn.update_progress_bar = function (progress, strTxt, style){
    /*if (typeof bar === "undefined")
        return false;*/
    
    var bar = $(this);
    bar.hide();
    bar.css('transition', 'none');
    bar.css('width', progress+'%').attr('aria-valuenow', progress); 
    
    if (style){
        bar.attr("class", "progress-bar "+style);
    }
    
    if (strTxt){
        if (progress === 100){
            bar.text(strTxt + progress + "%");
        }
        else
            bar.text(strTxt);
    }
    bar.show();
}

//Function to animate the progress bar
function animate_progress_bar(bar, strTxt){
    var progress;
    console.log("Animate progress bar is " + progress+'%');
    if (strTxt){
        bar.text(strTxt);
    }
    var animate = setInterval(function(){
        progress = parseInt(bar.attr('aria-valuenow'), 10)+1;
        if (progress >=100){
            clearInterval(animate);
        }
        bar.css('width', progress+'%').attr('aria-valuenow', progress); 
    }, 10);
}

//Function to add options to select list from an array
$.fn.add_select_options= function (options, ignore_list){
    
    var $_this = $(this);
    var selectList = $_this.find("select");
    
    selectList.each(function(){
        //Skip the select item which id is in the ignore list
        if ($.inArray($(this).attr('id'), ignore_list) !== -1){
            //console.log("Skip " + $(this).attr('id'));
            return;
        }
        var key = $(this).attr('id');
        var label = $_this.find(" label[for='"+ key +"']").text().trim();
      
        //Clear the select list first
        $(this).empty();
        
        $(this).append($("<option></option>")
        .attr("value",-1)
        .text("Choose the option"));  
        
        for (key in options){
            var value = options[key];
            var lower_value = value.toLowerCase();
            var lower_lable = label.toLowerCase();
            
            if (lower_lable.indexOf(lower_value) != -1){
                 $(this).append(
                     $("<option> selected</option>")
                    .attr("value",key)
                    .text(value)
                    .attr("selected", true))
            }
            else {
                $(this).append($("<option> </option>")
                .attr("value",key)
                .text(value));
            }
        }
    });
}

//Function to get all the select elements with their values
function get_select_val(){
    //console.log("Clicking...");
    var selectList = $("select");
    var tmpList = {};
    selectList.each(function(){
        var key = $(this).attr('id');
        //var val = parseInt($(this).val(), 10);
        var val = $(this).val();
        //console.log("Select " + key + ":" + val);
        if (val !== "Choose the option") {
            tmpList[key] = val;
        }
    });
    return tmpList;
}

//Function to get all the select elements with their text
$.fn.get_select_text = function(){
    var $_this = $(this);
    var selectList = $_this.find("select");
    var tmpList = {};
    selectList.each(function(){
        var key = $(this).attr('id');
        //var val = parseInt($(this).val(), 10);
        var val = $(this).find("option:selected").text();
        //console.log("Select " + key + ":" + val);
        if (val !== "Choose the option") {
            tmpList[key] = val;
            //console.log("The type of key is " + (typeof key));
            //console.log("Select " + key + ":" + val + " resultList is " + tmpList);
        }
    });
    return tmpList;
}

//Function to get the select id and label
$.fn.get_select_label = function(ignore_list){
    var $_this = $(this);
    var selectList = $_this.find("select");
    var tmpList = {};
    selectList.each(function(){
        var key = $(this).attr('id');
        
        if (ignore_list)
            if ($.inArray(key, ignore_list) !== -1)
                return;
        
        var val = $(this).find("option:selected").text().trim();
        if (val !== "Choose the option") 
        {
            val = $("label[for='"+ key +"']").text().trim();
            tmpList[key] = val;
        }
    });
    return tmpList;
}

//Function to cover any hh:mm string to 24 hours
function convert_to_24h(tm_str, default_tm){
    var hours, minutes, AMPM, tmp;
    minutes = 0;

    if (!tm_str)
        tm_str = default_tm;
    
    tmp = tm_str.match(/^(\d+)/);
    if (tmp){
        hours = Number(tmp[1]);
    }
    
    tmp = tm_str.match(/:(\d+)/);
    if (tmp) {
        minutes = Number(tmp[1]);
    }
    
    tmp = tm_str.match(/(AM|PM)/i);
    if (tmp) {
        AMPM = tmp[1].toUpperCase();
        if (AMPM === "PM" && hours < 12) hours = hours + 12;
        if (AMPM === "AM" && hours === 12) hours = hours - 12;
    }
    
    var sHours = hours.toString();
    var sMinutes = minutes.toString();
    if (hours < 10) sHours = "0" + sHours;
    if (minutes < 10) sMinutes = "0" + sMinutes;
    return (sHours + ":" + sMinutes);
}

//Function to convert the give date time to millisecond
function covert_to_second(date_str, tm_str){
    var tmp_str = date_str.concat(" ", tm_str);
    var tm = moment(tmp_str, "YYYY-MM-DD HH:mm").unix();
    return tm;
}

function form_async_submit($form, e, tb_params) {
    var $target = $($form.attr('data-target'));
    if (tb_params) {
        var table = $(tb_params.tb_id).DataTable();
    }
    e.preventDefault();
        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: $form.serialize(),
            success: function(data, status) {
                if (data.status === true) {
                    if (data.message) {
                        bootbox.alert(data.message, function(){
                            if (table) {
                                $target.modal('hide');
                                $form[0].reset();
                                table.ajax.reload();
                                var upload_table_id = $("#detele_table_id").val();
                                del_selected_row(upload_table_id);
                            }
                            else {
                                location.reload();
                            }
                        });
                    }
                    
                    if (data.redirect){
                         window.location.href = data.redirect;   
                    }
                }
                else {
                    if (data.message) {
                        bootbox.alert(data.message);
                    }
                }
            }
        });
}

function json_async_submit(tb_params, ajax_data){
    var table;
    if (tb_params.tb_id)
    {
        table = $(tb_params.tb_id).DataTable();
    }
    var posting = $.post(tb_params.ajax, ajax_data);
    posting.done(function(data){

        if (data.status === true) {
            if (data.message) {
                bootbox.alert(data.message, function(){
                    if (table) {
                        table.ajax.reload();
                    }
                    else {
                        location.reload();
                    }
                });
                }
            
            if (data.redirect){
                window.location.href = data.redirect;  
                }
            
            if (data.upload_return_data){
                show_upload_data(tb_params, data);   
            }
            }
        else {
            bootbox.alert(data.message);
        }
    });
}

function show_upload_data(tb_params, return_data){
    var fail_list = [];
    var success_list = []
    for (var idx =0; idx < return_data.upload_return_data.length; idx++){
        var record = return_data['upload_return_data'][idx]
        if (record.upload_status === true){
            success_list.push(record);
        }
        else {
            fail_list.push(record);   
        }
    }
    
    if (return_data['fail_cnt'] > 0){
        show_item("#upload_fail_panel");
        var upload_fail_tb_params = $.extend(true, {}, tb_params);
        upload_fail_tb_params.crud_tb_id = upload_fail_tb_params.tb_id;
        upload_fail_tb_params.tb_id = "#upload_fail_table";
        upload_fail_tb_params.edit_modal_id = upload_fail_tb_params.create_modal_id;
        upload_fail_tb_params.tableTools.tb_buttons = "edit_upload,export";
        upload_fail_tb_params.tableTools.aButtons = init_tb_btn(upload_fail_tb_params);
        upload_fail_tb_params.js_datasource = fail_list;
        //upload_fail_tb_params.upload_failed ;
        //print_obj(tb_params);
        init_upload_tb_cols(upload_fail_tb_params);
    }
    
}

function ajax_search(){
    var ajax_search_url = "ajax_search_url";
    var search_get_fields = "ajax_search_get_fields";
    var search_set_fields = "ajax_search_set_fields";
    //print_obj(search_set_fields);

    var formType = 'ajax_search';
    
    server_search($(this), 
                  ajax_search_url, 
                  search_get_fields, 
                  search_set_fields, 
                  formType);
}

function template_search(){
    
    var template_search_url = "template_search_url";
    var search_get_fields = "template_search_get_fields";
    var search_set_fields = "template_search_set_fields";
    var formType = 'template_search';
    server_search($(this), 
                  template_search_url, 
                  search_get_fields, 
                  search_set_fields, 
                  formType);
}

function server_search($current_field, search_url, search_get_fields, search_set_fields, form_type){
    var get_fields, set_fields;
    
    search_url = $("#"+search_url).val();
    var get_fields_str = $("#"+search_get_fields).val().trim();
    var set_fields_str = $("#"+search_set_fields).val().trim();
    if (get_fields_str !=""){
        get_fields = get_fields_str.split(',');
    }
    else {
        get_fields = null;   
    }
    
    if (set_fields_str !=""){
        set_fields = set_fields_str.split(',');
    }
    else {
        set_fields = null;   
    }
    
    //Get the search value from the form
    var search_data = {};
    
    //To get the current form, this is to make the get and set value from correct form
    var $current_form = $current_field.parents('form');
    search_data.formType = form_type;
    
    for (var idx = 0; idx < get_fields.length; idx++){
        var field_id = get_fields[idx];
        var field_val = $current_form.find('#'+field_id).val();
        
        /*if (field.is('select')){
            field_val = $('#'+field_id+" option:selected").val();
        }*/
        
        //console.log("value for " + field_id + " is " + field_val);
        search_data[field_id] = field_val;
    }
    //print_obj(search_data);
    var posting = $.post(search_url, search_data);
    
    posting.done(function(data){
        if (data != null) {
            if (data.ajax_search_message) {
                bootbox.alert(data.ajax_search_message);
            }
            data = data.data;
        }
        
        if (set_fields==null)
            return;
        
        if (data == null)
            return;
        
        var field_data=null, datalist=null;
        if ($.isArray(data)){
            if (data.length == 1) {
                field_data = data[0];
            }
            else{
                field_data = null;   
            }
            
            if (data.length > 1) {
                datalist = data;
            }
        }
        else {
            field_data = data;   
        }
        
        for (var idx = 0; idx < set_fields.length; idx++){
            var field_id = set_fields[idx];
            var current_field = $current_form.find('#'+field_id);
            
            if (data.ajax_error_message){
                current_field.val("");  
                }
            else {
                if (datalist != null){
                    var datalist_field=$current_form.find('#'+field_id+'_datalist');                       var datalist_opts = "";
                    var opt_list = [];
                    for (var list_idx = 0; list_idx < datalist.length; list_idx++)
                    {
                        var cur_rec = datalist[list_idx];
                        var opt_val = cur_rec[field_id];
                        if (opt_val == null)
                            continue;
                        //Make sure it's a distinct value
                        if (opt_list.indexOf(opt_val) == -1){
                            datalist_opts = datalist_opts + "<option value='"+opt_val+"'></option>";
                            opt_list.push(opt_val);
                        }
                    }
                    datalist_field.children().remove().end().append(datalist_opts);
                }
                if (field_data == null){
                    continue;    
                }
                
                else if (field_id in field_data){
                    var field_val = field_data[field_id];
                    var field_type = current_field.prop('type');
                    if (field_type == 'select-one'){
                        var sel_query = "option:contains('"+field_val+"')";
                        current_field.find(sel_query).prop('selected', true);
                    }
                    else{
                        current_field.val(field_val);
                    }
                }

            }
        }
    });    
}

function create_new_field(add_btn){
    var wrapper = add_btn.parent('div'); //Fields wrapper
    var field_id = wrapper.find("#repeatFieldName").val(); //Add button ID
    //console.log('adding fiels:'+field_id);
    var new_div = "<div><a href='#' class='remove_field col-md-3 col-md-offset-1'>Remove</a></div>"
    var new_field = wrapper.find('#'+field_id+':first').clone();
    wrapper.append(new_div);    
    var $new_div = wrapper.find('div:last')
    $new_div.append(new_field);
    
    $('.remove_field').click(function(e){
        e.preventDefault();
        $(this).parent('div').remove(); 
    });
    
    return new_field;
}

function refresh_task_set_options(uploaded_task,
                                all_task,
                                task_set_field_list){
    var task_set_field;

    //Add the new task to the options
    for (var idx=0; idx<uploaded_task.length; idx++){
        var new_task = uploaded_task[idx].task_id;
        for (var task_idx=0; task_idx<all_task.length; task_idx++){
            var check_task = all_task[task_idx];
            
            //If the new_task is in the all_task list
            if (check_task.task_id == new_task){
                //Add option to #task_set
                
                //For each task_set field
                for (var field_idx=0; 
                     field_idx < task_set_field_list.length; 
                     field_idx++)
                {
                    task_set_field = task_set_field_list[field_idx];
                    
                    //Check if the task is already in the list
                    var sel_query = "option[value='"+check_task._entity_id+"']";
                    var field_option = task_set_field.find(sel_query);
                    
                    //If yes, set the selected status to 'true'
                    if (field_option.length > 0) {
                        field_option.prop('selected', true);
                    }
                    //If not, add the new option in the field
                    else {
                        task_set_field.append(
                            $("<option></option>")
                            .attr("value",check_task._entity_id)
                            .text(check_task.task_id)
                            .attr("selected", true));                  
                    }
                }
                all_task.splice(task_idx,1);
                break;
            }
        }
    }
    
    //Refresh the duallistbox
    for (var field_idx=0; field_idx < task_set_field_list.length; field_idx++)
    {
        task_set_field = task_set_field_list[field_idx];
        task_set_field.bootstrapDualListbox('refresh');
        //task_set_field.trigger("chosen:updated");   
    }    
}

function reset_current_form(){
    var $current_field = $(this);
    var $current_form = $current_field.parents('form');
    $current_form[0].reset();
}

