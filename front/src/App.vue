<template>
  <RouterView />
</template>

<style>
:root {
  --cae-bg: #edf1f5;
  --cae-panel: #ffffff;
  --cae-panel-soft: #f6f8fb;
  --cae-ink: #172234;
  --cae-muted: #667386;
  --cae-line: #ccd5e1;
  --cae-line-strong: #9eacbc;
  --cae-blue-900: #071f3f;
  --cae-blue-800: #0d3c76;
  --cae-blue-700: #15559f;
  --cae-blue-600: #1167c9;
  --cae-blue-100: #e8f1ff;
  --cae-cyan: #20a8db;
  --cae-good: #0b8f67;
  --cae-warn: #b56b00;
  --cae-danger: #c83737;
  --el-border-radius-base: 4px;
  --el-border-radius-small: 3px;
  --el-border-radius-round: 999px;
  --el-color-primary: #1167c9;
  --el-font-size-base: 13px;
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
}

body {
  margin: 0;
  overflow: hidden;
  background: var(--cae-bg);
  color: var(--cae-ink);
  font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
  letter-spacing: 0;
}

button,
input,
textarea,
select {
  font: inherit;
}

.el-button,
.el-input__wrapper,
.el-input-number,
.el-input-number .el-input__wrapper,
.el-select__wrapper,
.el-upload-dragger,
.el-alert,
.el-tag {
  border-radius: 4px !important;
}

.el-form-item {
  margin-bottom: 10px;
}

.el-form-item__label {
  color: var(--cae-muted);
  font-size: 12px;
  line-height: 1.2;
  padding-bottom: 4px;
}

.el-input-number {
  width: 100%;
}

.el-button {
  padding: 8px 12px;
}

.el-button + .el-button {
  margin-left: 6px;
}

.el-segmented {
  --el-segmented-item-selected-bg-color: var(--cae-blue-800);
  --el-segmented-item-selected-color: #fff;
  border-radius: 4px;
}
</style>
