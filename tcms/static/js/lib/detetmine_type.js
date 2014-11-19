function isNumber(obj) {
	return (typeof obj == 'number') && obj.constructor == Number;
}

function isArray(obj) {
	return (typeof obj == 'object') && obj.constructor == Array;
}


function isString(str) {
	return (typeof str == 'string') && str.constructor == String;
}

function isDate(obj) {
	return (typeof obj == 'object') && obj.constructor == Date;
}

function isFunction(obj) {
	return (typeof obj == 'function') && obj.constructor == Function;
}

function isObject(obj) {
	return (typeof obj == 'object') && obj.constructor == Object;
}
