const path = require('path')

module.exports = {
    mode: 'none',
    entry: [
        './bugs/static/bugs/js/index.js',
        './management/static/management/js/build_admin.js',
        './static/js/index.js',
        './static/js/simplemde_security_override.js',
        './telemetry/static/telemetry/js/testing/index.js',
        './testcases/static/testcases/js/index.js',
        './testplans/static/testplans/js/index.js',
        './testruns/static/testruns/js/index.js',
    ],
    resolve: {
        modules: [
            path.join(__dirname, 'static'),
            'node_modules',
        ],
    },
    output: {
        path: path.join(__dirname, 'static', 'js'),
        filename: 'bundle.js'
    },
}
