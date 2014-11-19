// ===================================================================
// Author: Matt Kruse <matt@mattkruse.com>
// WWW: http://www.mattkruse.com/
//
// NOTICE: You may use this code for any purpose, commercial or
// private, without any further permission from the author. You may
// remove this notice from your final code if you wish, however it is
// appreciated by the author if at least my web site address is kept.
//
// You may *NOT* re-distribute this code in any way except through its
// use. That means, you can include it in your product, or your web
// site, or any other form where the code is actually being used. You
// may not put the plain javascript up on your site for download or
// include it in your javascript libraries for download. 
// If you wish to share this code with others, please just point them
// to the URL instead.
// Please DO NOT link directly to my .js files from your site. Copy
// the files to your server and use them there. Thank you.
//
// According to the author, "you can use [this code] however you want,
// without restrictions" (email from Matt Kruse to Xuqing Kuang dated
// April 4, 2010).
// ===================================================================

function LTrim(str){if(str==null){return null;}for(var i=0;str.charAt(i)==" ";i++);return str.substring(i,str.length);}
function RTrim(str){if(str==null){return null;}for(var i=str.length-1;str.charAt(i)==" ";i--);return str.substring(0,i+1);}
function Trim(str){return LTrim(RTrim(str));}
function LTrimAll(str){if(str==null){return str;}for(var i=0;str.charAt(i)==" " || str.charAt(i)=="\n" || str.charAt(i)=="\t";i++);return str.substring(i,str.length);}
function RTrimAll(str){if(str==null){return str;}for(var i=str.length-1;str.charAt(i)==" " || str.charAt(i)=="\n" || str.charAt(i)=="\t";i--);return str.substring(0,i+1);}
function TrimAll(str){return LTrimAll(RTrimAll(str));}
function isNull(val){return(val==null);}
function isBlank(val){if(val==null){return true;}for(var i=0;i<val.length;i++){if((val.charAt(i)!=' ')&&(val.charAt(i)!="\t")&&(val.charAt(i)!="\n")&&(val.charAt(i)!="\r")){return false;}}return true;}
function isInteger(val){if(isBlank(val)){return false;}for(var i=0;i<val.length;i++){if(!isDigit(val.charAt(i))){return false;}}return true;}
function isNumeric(val){return(parseFloat(val,10)==(val*1));}
function isArray(obj){return(typeof(obj.length)=="undefined")?false:true;}
function isDigit(num){if(num.length>1){return false;}var string="1234567890";if(string.indexOf(num)!=-1){return true;}return false;}
function setNullIfBlank(obj){if(isBlank(obj.value)){obj.value="";}}
function setFieldsToUpperCase(){for(var i=0;i<arguments.length;i++){arguments[i].value = arguments[i].value.toUpperCase();}}
function disallowBlank(obj){var msg=(arguments.length>1)?arguments[1]:"";var dofocus=(arguments.length>2)?arguments[2]:false;if(isBlank(getInputValue(obj))){if(!isBlank(msg)){alert(msg);}if(dofocus){if(isArray(obj) &&(typeof(obj.type)=="undefined")){obj=obj[0];}if(obj.type=="text"||obj.type=="textarea"||obj.type=="password"){obj.select();}obj.focus();}return true;}return false;}
function disallowModify(obj){var msg=(arguments.length>1)?arguments[1]:"";var dofocus=(arguments.length>2)?arguments[2]:false;if(getInputValue(obj)!=getInputDefaultValue(obj)){if(!isBlank(msg)){alert(msg);}if(dofocus){if(isArray(obj) &&(typeof(obj.type)=="undefined")){obj=obj[0];}if(obj.type=="text"||obj.type=="textarea"||obj.type=="password"){obj.select();}obj.focus();}setInputValue(obj,getInputDefaultValue(obj));return true;}return false;}
function commifyArray(obj,delimiter){if(typeof(delimiter)=="undefined" || delimiter==null){delimiter = ",";}var s="";if(obj==null||obj.length<=0){return s;}for(var i=0;i<obj.length;i++){s=s+((s=="")?"":delimiter)+obj[i].toString();}return s;}
function getSingleInputValue(obj,use_default,delimiter){switch(obj.type){case 'radio': case 'checkbox': return(((use_default)?obj.defaultChecked:obj.checked)?obj.value:null);case 'text': case 'hidden': case 'textarea': return(use_default)?obj.defaultValue:obj.value;case 'password': return((use_default)?null:obj.value);case 'select-one':
if(obj.options==null){return null;}if(use_default){var o=obj.options;for(var i=0;i<o.length;i++){if(o[i].defaultSelected){return o[i].value;}}return o[0].value;}if(obj.selectedIndex<0){return null;}return(obj.options.length>0)?obj.options[obj.selectedIndex].value:null;case 'select-multiple':
if(obj.options==null){return null;}var values=new Array();for(var i=0;i<obj.options.length;i++){if((use_default&&obj.options[i].defaultSelected)||(!use_default&&obj.options[i].selected)){values[values.length]=obj.options[i].value;}}return(values.length==0)?null:commifyArray(values,delimiter);}alert("FATAL ERROR: Field type "+obj.type+" is not supported for this function");return null;}
function getSingleInputText(obj,use_default,delimiter){switch(obj.type){case 'radio': case 'checkbox': 	return "";case 'text': case 'hidden': case 'textarea': return(use_default)?obj.defaultValue:obj.value;case 'password': return((use_default)?null:obj.value);case 'select-one':
if(obj.options==null){return null;}if(use_default){var o=obj.options;for(var i=0;i<o.length;i++){if(o[i].defaultSelected){return o[i].text;}}return o[0].text;}if(obj.selectedIndex<0){return null;}return(obj.options.length>0)?obj.options[obj.selectedIndex].text:null;case 'select-multiple':
if(obj.options==null){return null;}var values=new Array();for(var i=0;i<obj.options.length;i++){if((use_default&&obj.options[i].defaultSelected)||(!use_default&&obj.options[i].selected)){values[values.length]=obj.options[i].text;}}return(values.length==0)?null:commifyArray(values,delimiter);}alert("FATAL ERROR: Field type "+obj.type+" is not supported for this function");return null;}
function setSingleInputValue(obj,value){switch(obj.type){case 'radio': case 'checkbox': if(obj.value==value){obj.checked=true;return true;}else{obj.checked=false;return false;}case 'text': case 'hidden': case 'textarea': case 'password': obj.value=value;return true;case 'select-one': case 'select-multiple':
var o=obj.options;for(var i=0;i<o.length;i++){if(o[i].value==value){o[i].selected=true;}else{o[i].selected=false;}}return true;}alert("FATAL ERROR: Field type "+obj.type+" is not supported for this function");return false;}
function getInputValue(obj,delimiter){var use_default=(arguments.length>2)?arguments[2]:false;if(isArray(obj) &&(typeof(obj.type)=="undefined")){var values=new Array();for(var i=0;i<obj.length;i++){var v=getSingleInputValue(obj[i],use_default,delimiter);if(v!=null){values[values.length]=v;}}return commifyArray(values,delimiter);}return getSingleInputValue(obj,use_default,delimiter);}
function getInputText(obj,delimiter){var use_default=(arguments.length>2)?arguments[2]:false;if(isArray(obj) &&(typeof(obj.type)=="undefined")){var values=new Array();for(var i=0;i<obj.length;i++){var v=getSingleInputText(obj[i],use_default,delimiter);if(v!=null){values[values.length]=v;}}return commifyArray(values,delimiter);}return getSingleInputText(obj,use_default,delimiter);}
function getInputDefaultValue(obj,delimiter){return getInputValue(obj,delimiter,true);}
function isChanged(obj){return(getInputValue(obj)!=getInputDefaultValue(obj));}
function setInputValue(obj,value){var use_default=(arguments.length>1)?arguments[1]:false;if(isArray(obj)&&(typeof(obj.type)=="undefined")){for(var i=0;i<obj.length;i++){setSingleInputValue(obj[i],value);}}else{setSingleInputValue(obj,value);}}
function isFormModified(theform,hidden_fields,ignore_fields){if(hidden_fields==null){hidden_fields="";}if(ignore_fields==null){ignore_fields="";}var hiddenFields=new Object();var ignoreFields=new Object();var i,field;var hidden_fields_array=hidden_fields.split(',');for(i=0;i<hidden_fields_array.length;i++){hiddenFields[Trim(hidden_fields_array[i])]=true;}var ignore_fields_array=ignore_fields.split(',');for(i=0;i<ignore_fields_array.length;i++){ignoreFields[Trim(ignore_fields_array[i])]=true;}for(i=0;i<theform.elements.length;i++){var changed=false;var name=theform.elements[i].name;if(!isBlank(name)){var type=theform.elements[i].type;if(!ignoreFields[name]){if(type=="hidden"&&hiddenFields[name]){changed=isChanged(theform[name]);}else if(type=="hidden"){changed=false;}else{changed=isChanged(theform[name]);}}}if(changed){return true;}}return false;}

