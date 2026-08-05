# novel

Python 抓取小说生成 ePub

## 环境准备

依赖用 [uv](https://docs.astral.sh/uv/) 管理：

```bash
uv sync
```

## 使用

```bash
uv run novel.py <小说目录页URL> [--thread 10]
```

生成的文件在 `epub/` 下。已下载的章节会跳过，中断后重跑可以续传。

## 验证规则

改完 `novel.json` 后先验证，只抓详情页、目录页和一章正文：

```bash
uv run novel.py <小说目录页URL> --check [--chapter 0]
```

会逐条打出规则的命中结果，全部命中时退出码为 0。

## 站点规则

规则写在 `novel.json`，按域名匹配。两种写法：

- CSS 选择器加 `@属性`，如 `a@href`、`div.content@text`（`@text` 取文本）
- `re:` 前缀走正则，匹配整个页面源码的第一个捕获组

字段：

| 字段                                 | 说明                                             |
| ------------------------------------ | ------------------------------------------------ |
| `siteUrl`                            | 按域名匹配用                                     |
| `charset`                            | 页面编码，默认 `utf-8`                           |
| `isBiquge`                           | 笔趣阁系站点，书籍信息直接读 `og:novel:*` 元信息 |
| `ruleName`                           | 书籍信息-名称，在 `isBiquge` 时不需要书籍信息    |
| `ruleCover`                          | 书籍信息-封面                                    |
| `ruleAuthor`                         | 书籍信息-作者                                    |
| `ruleCategory`                       | 书籍信息-分类                                    |
| `ruleChapterUrl`                     | 目录页地址，留空表示目录就在详情页上             |
| `ruleChapterItems`                   | 选中目录里每个章节条目                           |
| `ruleChapterName` / `ruleContentUrl` | 在条目内取章节名和链接                           |
| `ruleChapterContent`                 | 正文所在元素                                     |
| `ruleIgnoreLines`                    | 正文里要丢掉的行，命中即整行删除                 |