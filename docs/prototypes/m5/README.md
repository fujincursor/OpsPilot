# M5 模块 - 页面原型

本目录为 **M5 Bug 修复流程** 的静态 HTML 页面原型，样式遵循 [《页面原型风格规范》](../../页面原型风格规范.md)。

## 如何查看

在浏览器中直接打开各 HTML 文件即可（建议从 `bug-list.html` 进入）。

## 页面与文件对应

| 页面 | 文件 |
|------|------|
| P1 Bug 工单列表 | [bug-list.html](bug-list.html) |
| P2 Bug 工单详情 | [bug-detail.html](bug-detail.html) |
| P3 修复方案（已生成） | [fix-plan.html](fix-plan.html) |
| P3 修复方案（待生成） | [fix-plan-empty.html](fix-plan-empty.html) |
| P3 修复方案（生成中） | [fix-plan-generating.html](fix-plan-generating.html) |
| P3 修复方案（生成失败） | [fix-plan-failed.html](fix-plan-failed.html) |

## 样式说明

- 共用样式：`style.css`（色彩、字体、间距、组件均按风格规范实现）
- 页面间通过 `<a href="...">` 链接跳转，便于按流程浏览

## 详细说明

参见 [M5-页面原型说明.md](../../M5-页面原型说明.md)。
