import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import pluginVue from 'eslint-plugin-vue';

export default [
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'coverage/**',
      'playwright-report/**',
      'test-results/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },
  {
    files: ['**/*.{ts,vue}'],
    rules: {
      'vue/multi-word-component-names': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      // ESLint 9.12 no-useless-assignment 对 Vue 3 ref()/shallowRef() 模式有 false positive
      // 见 https://github.com/eslint/eslint/issues/18636 （open at 2026-07）
      // 关闭直至上游修复；本仓库 ref 模式均为合理响应式状态写入。
      'no-useless-assignment': 'off',
      // 以下三条 vue/* 规则与 Prettier 在 printWidth 100 下存在格式冲突
      // （Prettier 倾向单行/合并属性，规则要求每属性单行/内容强制换行）。
      // eslint-plugin-vue 官方建议使用 Prettier 时关闭，格式以 Prettier 为准。
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/multiline-html-element-content-newline': 'off',
    },
  },
  {
    files: ['**/*.spec.ts', '**/*.test.ts', 'tests/**'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },
];
