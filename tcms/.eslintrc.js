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
    rules: {
        indent: ['error', 4],
        'no-undef': 'off',
        'node/no-callback-literal': 'off'
    }
}
