module.exports = {
    env: {
        browser: true,
        es2021: true
    },
    extends: [
        'standard'
    ],
    parserOptions: {
        ecmaVersion: 12
    },
    ignorePatterns: ['static/js/bundle.js'],
    rules: {
        indent: ['error', 4],
        'no-undef': 'off',
        'node/no-callback-literal': 'off'
    }
}
