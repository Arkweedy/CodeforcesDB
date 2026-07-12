# WebUI 视觉基准

实现基准图：[webui-cyan-concept.png](webui-cyan-concept.png)。

核心原则：

- 暖白画布、白色面板、深蓝灰正文和浅青灰边框。
- 低饱和青色用于主交互和选中态，浅蓝用于信息状态。
- 樱色只用于收藏、非常重要和少量警告；粉色只作为轻微备注边框。
- 选中题目使用浅青灰底和左侧细青线，不使用整行粉色。
- Codeforces Rating 保留原有色段。

主要 token 定义在 `web/src/styles.css` 的 `:root` 中。

## 实现验收截图

- [桌面列表](webui-qa-desktop.png)：1536×1024 viewport。
- [桌面三栏详情](webui-qa-desktop-detail.png)：1536×1024 viewport。
- [平板列表](webui-qa-tablet.png)：1024×768 viewport，筛选入口改为抽屉。
- [手机卡片](webui-qa-mobile.png)：390×844 viewport。
- [手机全屏详情](webui-qa-mobile-detail.png)：390×844 viewport。

PNG 的实际像素边界可能因浏览器滚动条占位略小于 viewport；截图时已通过
`window.innerWidth` 与响应式 CSS 的计算样式核验断点。
