import type { Importance, RatingStatus, Stats } from "./types";
import FULL_TAG_TEXT_ZH from "./i18n/tags.zh.json";

export type Locale = "zh" | "en";

export const DEFAULT_LOCALE: Locale = "zh";
const STORAGE_KEY = "cfdb.locale";

type UiKey =
  | "aliases"
  | "annotation"
  | "codeforces"
  | "complexity"
  | "confidence"
  | "constraints"
  | "contest"
  | "coreIdea"
  | "empty"
  | "favorite"
  | "favorites"
  | "importance"
  | "loading"
  | "note"
  | "personal"
  | "problem"
  | "problemset"
  | "rating"
  | "ratingMax"
  | "ratingMin"
  | "ratingStatus"
  | "save"
  | "search"
  | "solutionVariants"
  | "sources"
  | "status"
  | "tags"
  | "text";

const UI_TEXT: Record<Locale, Record<UiKey, string>> = {
  zh: {
    aliases: "别名入口",
    annotation: "题目分析",
    codeforces: "Codeforces",
    complexity: "复杂度",
    confidence: "可信度",
    constraints: "约束",
    contest: "比赛",
    coreIdea: "核心思路",
    empty: "没有匹配题目。",
    favorite: "收藏",
    favorites: "收藏",
    importance: "重要性",
    loading: "加载中",
    note: "备注",
    personal: "个人",
    problem: "题目",
    problemset: "题库入口",
    rating: "评分",
    ratingMax: "最高分",
    ratingMin: "最低分",
    ratingStatus: "评分状态",
    save: "保存",
    search: "搜索",
    solutionVariants: "解法",
    sources: "来源",
    status: "状态",
    tags: "标签",
    text: "文本"
  },
  en: {
    aliases: "Aliases",
    annotation: "Annotation",
    codeforces: "Codeforces",
    complexity: "Complexity",
    confidence: "Confidence",
    constraints: "Constraints",
    contest: "Contest",
    coreIdea: "Core Idea",
    empty: "No matching problems.",
    favorite: "Favorite",
    favorites: "Favorites",
    importance: "Importance",
    loading: "Loading",
    note: "Note",
    personal: "Personal",
    problem: "Problem",
    problemset: "Problemset",
    rating: "Rating",
    ratingMax: "Rating max",
    ratingMin: "Rating min",
    ratingStatus: "Rating Status",
    save: "Save",
    search: "Search",
    solutionVariants: "Solution Variants",
    sources: "Sources",
    status: "Status",
    tags: "Tags",
    text: "Text"
  }
};

const IMPORTANCE_TEXT: Record<Locale, Record<Importance, string>> = {
  zh: {
    primary: "主标签",
    secondary: "次标签",
    incidental: "附带"
  },
  en: {
    primary: "Primary",
    secondary: "Secondary",
    incidental: "Incidental"
  }
};

const RATING_STATUS_TEXT: Record<Locale, Record<RatingStatus, string>> = {
  zh: {
    official: "官方评分",
    pending_cf_rating: "等待 CF 评分",
    no_cf_rating: "无 CF 评分",
    unknown: "未知"
  },
  en: {
    official: "Official",
    pending_cf_rating: "Pending CF rating",
    no_cf_rating: "No CF rating",
    unknown: "Unknown"
  }
};

const GENERIC_VALUE_TEXT: Record<Locale, Record<string, string>> = {
  zh: {
    "accepted-code": "通过代码",
    accepted_code: "通过代码",
    accepted_submission: "通过提交",
    "auto-seeded": "自动种子",
    auto_seeded: "自动种子",
    blog: "博客",
    candidate: "候选",
    contest: "赛事档案",
    cfstep_hints: "CFStep 提示",
    "div1-div2-overlap": "Div.1/Div.2 重题",
    editorial: "题解",
    excluded: "已排除",
    high: "高",
    independent_code: "独立代码",
    "luogu-solution": "洛谷题解",
    luogu_problem: "洛谷题面",
    luogu_solution: "洛谷题解",
    low: "低",
    main: "主解法",
    medium: "中",
    needs_manual_review: "需要人工复核",
    reviewed: "已复核",
    secondary: "次解法",
    self_derivation: "自行推导",
    statement: "题面",
    statement_mirror: "题面镜像",
    status: "提交状态"
  },
  en: {
    "accepted-code": "Accepted code",
    accepted_code: "Accepted code",
    accepted_submission: "Accepted submission",
    "auto-seeded": "Auto seeded",
    auto_seeded: "Auto seeded",
    blog: "Blog",
    candidate: "Candidate",
    contest: "Contest archive",
    cfstep_hints: "CFStep hints",
    "div1-div2-overlap": "Div.1/Div.2 overlap",
    editorial: "Editorial",
    excluded: "Excluded",
    high: "High",
    independent_code: "Independent code",
    "luogu-solution": "Luogu solutions",
    luogu_problem: "Luogu problem",
    luogu_solution: "Luogu solutions",
    low: "Low",
    main: "Main",
    medium: "Medium",
    needs_manual_review: "Needs manual review",
    reviewed: "Reviewed",
    secondary: "Secondary",
    self_derivation: "Self derivation",
    statement: "Statement",
    statement_mirror: "Statement mirror",
    status: "Submission status"
  }
};


const SEGMENT_TEXT_ZH: Record<string, string> = {
  "2-sat": "2-SAT",
  "acam": "AC 自动机",
  "algorithm": "算法",
  "alternating-sign-transform": "交替符号变换",
  "argmin-interval-compression": "最优区间压缩",
  "arboricity": "森林分解数",
  "articulation-point": "割点",
  "automaton-dp": "自动机 DP",
  "batch-simulation": "批量模拟",
  "back-edge-enumeration": "返祖边枚举",
  "bayesian-update": "贝叶斯更新",
  "bayesian-search": "贝叶斯搜索",
  "bfs": "BFS",
  "binary-lifting": "倍增",
  "binary-search": "二分",
  "binary-carry": "二进制进位",
  "binomial-identity": "二项式恒等式",
  "binomial-parity": "二项式奇偶性",
  "bipartite-graph": "二分图",
  "bipartite-double-cover": "二分双覆盖",
  "bitmask": "位掩码",
  "bitmask-dp": "状压 DP",
  "bitset": "Bitset 位集",
  "bitwise-greedy": "按位贪心",
  "border": "Border",
  "boruvka": "Borůvka 算法",
  "bridge": "桥",
  "brute-force": "暴力",
  "burnside-lemma": "Burnside 引理",
  "bottleneck-path": "瓶颈路径",
  "bounding-box": "轴对齐包围盒",
  "cartesian-tree": "笛卡尔树",
  "canonical-form": "规范形",
  "candidate-pruning": "候选剪枝",
  "case-analysis": "分类讨论",
  "cactus": "仙人掌",
  "catalan": "Catalan 数",
  "centroid-decomposition": "点分治",
  "chain-graph": "链图",
  "chain-decomposition": "DAG 链分解",
  "chinese-remainder-theorem": "中国剩余定理",
  "chip-firing": "Chip-firing（筹码分发）",
  "circular-interval": "环形区间",
  "classify-overlap": "重叠分类",
  "combinatorics": "组合数学",
  "component-decomposition": "分量分解",
  "coordinate-compression": "坐标压缩",
  "contiguous-reachable-range": "连续可达值域",
  "communication": "通信",
  "connectivity": "连通性",
  "constructive": "构造",
  "convolution": "卷积",
  "counting-dp": "计数 DP",
  "cycle-space": "环空间",
  "convert-to-prefix": "转为前缀",
  "cycle-detection": "判环",
  "convex-hull": "凸包",
  "convex-layers": "凸包层",
  "convex-hull-optimization": "斜率优化",
  "constraint-relaxation": "约束放宽",
  "data-structure": "数据结构",
  "dag": "DAG",
  "decision-tree": "决策树",
  "degree-sequence": "度数序列",
  "difference-array": "差分数组",
  "dfs": "DFS",
  "dfs-order": "DFS 序",
  "digit-dp": "数位 DP",
  "dijkstra": "Dijkstra",
  "dominating-set": "支配集",
  "difference-transform": "差分转化",
  "distance-signature": "距离签名",
  "dyadic-interval-decomposition": "二进制区间分解",
  "divide-and-conquer": "分治",
  "divisibility": "整除",
  "divisor-enumeration": "因子枚举",
  "divisor-sieve": "因子筛",
  "dp": "动态规划",
  "dsu": "并查集",
  "du-sieve": "杜教筛",
  "endpoint-reduction": "端点化简",
  "egf": "指数生成函数",
  "entropy": "熵",
  "euler-phi": "欧拉函数",
  "eulerian-number": "欧拉数",
  "expected-progress": "期望推进",
  "exchange-argument": "交换论证",
  "expression": "表达式",
  "extreme-position": "极端位置",
  "euler-trail": "欧拉路径",
  "euler-tour": "欧拉序",
  "edge-orientation": "边定向",
  "fenwick-tree": "树状数组",
  "fibonacci": "Fibonacci 数论",
  "finite-state-dp": "有限状态 DP",
  "floyd-warshall": "Floyd-Warshall",
  "fft": "FFT",
  "and-fwt": "AND FWT",
  "finite-automaton": "有限自动机",
  "formal-grammar": "形式文法",
  "flow": "网络流",
  "functional-graph": "函数图",
  "fwt": "FWT",
  "game-theory": "博弈论",
  "gcd": "GCD",
  "gcd-convolution": "GCD 卷积",
  "generating-function": "生成函数",
  "geometry": "几何",
  "graph": "图论",
  "grid-separator": "网格分隔链",
  "graph-dp": "图上 DP",
  "greedy": "贪心",
  "regret-greedy": "反悔贪心",
  "grid-dp": "网格 DP",
  "group-by-divisor": "按因子分组",
  "handle-special-case": "特判",
  "half-plane-intersection": "半平面交",
  "hash-map": "哈希表",
  "hashing": "哈希",
  "harmonic-sum": "调和级数枚举",
  "hamiltonian-path": "哈密顿路径",
  "heavy-light-decomposition": "树链剖分",
  "helper-buffer": "辅助缓冲",
  "highest-differing-bit": "最高不同位",
  "implementation": "实现",
  "implicit-sequence": "隐式序列",
  "inclusion-exclusion": "容斥",
  "interactive": "交互",
  "interleaving": "字符串交织",
  "invariant": "不变量",
  "inequality": "不等式",
  "information-theory": "信息论",
  "information-encoding": "信息编码",
  "interval-feasibility": "区间可行性",
  "interval-union": "区间并集",
  "interval-edge-coloring": "区间边染色",
  "conflict-free-coloring": "无冲突染色",
  "kmp-prefix-function": "KMP 前缀函数",
  "knapsack-dp": "背包 DP",
  "layered-graph": "分层图",
  "lexicographic-order": "字典序",
  "lca": "最近公共祖先",
  "lcm-convolution": "LCM 卷积",
  "line-graph": "线图",
  "line-metric": "一维线度量",
  "lazy-affine-update": "懒惰仿射更新",
  "lazy-deletion": "懒删除",
  "lazy-propagation": "懒标记",
  "lattice-points": "格点计数",
  "lattice-path-counting": "单调格路计数",
  "li-chao-tree": "李超线段树",
  "linear-algebra": "线性代数",
  "linear-diophantine-equation": "线性丢番图方程",
  "linear-system": "线性方程组",
  "linear-objective-extreme-choice": "线性目标取端点",
  "linearity-of-expectation": "期望线性性",
  "lis-dp": "LIS/非降子序列 DP",
  "lowbit": "Lowbit",
  "lower-bound-flow": "下界流",
  "maintain-contribution": "维护贡献",
  "mark-multiples": "标记倍数",
  "max-cut": "最大割",
  "matching": "匹配",
  "maximum-count-bound": "最大数量上界",
  "maximum-path": "最大路径",
  "math": "数学",
  "matrix": "矩阵",
  "matrix-exponentiation": "矩阵快速幂",
  "majority-vote": "多数投票",
  "max-subarray": "最大子段和",
  "modular-arithmetic": "模运算",
  "meet-in-the-middle": "折半搜索",
  "median-alignment": "中位数对齐",
  "median-threshold": "中位数阈值",
  "misra-gries": "Misra-Gries",
  "nearest-occurrence": "最近出现位置",
  "minmax": "Min-Max",
  "minimax": "Minimax",
  "misere-nim": "反常 Nim",
  "minkowski-sum": "闵可夫斯基和",
  "min-cost-flow": "最小费用流",
  "convex-cost-flow": "凸费用流",
  "min-cost-perfect-matching": "最小费用完美匹配",
  "min-max-convolution": "Min-Max 卷积",
  "min-plus-convolution": "Min-Plus 卷积",
  "min25-sieve": "Min_25 筛",
  "mobius": "莫比乌斯",
  "mobius-inversion": "莫比乌斯反演",
  "monotonic-queue": "单调队列",
  "monotonic-stack": "单调栈",
  "monotonicity": "单调性",
  "mst": "最小生成树",
  "multinomial": "多项式系数",
  "multiplicative-order": "乘法阶",
  "next-pointer": "next 指针",
  "non-overlap": "不重叠选择",
  "number-theory": "数论",
  "offline": "离线",
  "odd-even-transposition-sort": "奇偶换位排序",
  "online": "在线",
  "one-parameter-optimization": "单参数优化",
  "oracle-design": "查询设计",
  "ordered-multiset": "有序可重集",
  "order-statistics-tree": "顺序统计树",
  "paradigm": "范式",
  "parity": "奇偶性",
  "partition-dp": "分段 DP",
  "p-position-characterization": "必败态刻画",
  "parsing": "解析",
  "palindrome": "回文",
  "parallel-binary-search": "整体二分",
  "program-synthesis": "程序合成",
  "path-counting": "路径计数",
  "permutation-counting": "排列计数",
  "permutation-structure": "排列结构",
  "periodicity": "周期性",
  "piecewise-constant": "分段常值压缩",
  "pigeonhole-principle": "鸽巢原理",
  "polygon-inequality": "多边形不等式",
  "polynomial-interpolation": "多项式插值",
  "popcount-invariant": "popcount 不变量",
  "prefix-max-optimization": "前缀最大值优化",
  "prefix-suffix-extrema": "前后缀极值",
  "probability-dp": "概率 DP",
  "prefix-sum-optimization": "前缀和优化",
  "prefix-sums": "前缀和",
  "priority-queue": "优先队列",
  "persistent-balanced-tree": "可持久化平衡树",
  "persistent-segment-tree": "可持久化线段树",
  "prime-factor-count": "质因子计数",
  "prime-factorization": "质因数分解",
  "probability": "概率",
  "prufer-sequence": "Prüfer 序列",
  "queue": "队列",
  "radix-sort": "基数排序",
  "randomized": "随机化算法",
  "ramsey-theory": "Ramsey 理论",
  "quadtree": "四叉树",
  "quotient-state-space": "商状态空间",
  "query-differencing": "查询差分",
  "residual-cycle": "残量环调整",
  "retrograde-analysis": "逆向状态分析",
  "rotational-symmetry": "旋转对称",
  "residue-knapsack": "同余背包",
  "rolling-hash": "滚动哈希",
  "run-length-encoding": "游程编码",
  "rollback": "可回滚",
  "reverse-process": "逆向处理",
  "rook-graph": "车图",
  "scheduling": "调度",
  "scc": "强连通分量",
  "self-modifying-code": "自修改代码",
  "deadline-greedy": "截止时间贪心",
  "search": "搜索",
  "segmentation": "分段",
  "segment-tree": "线段树",
  "segmented-sieve": "分段筛",
  "series-parallel-graph": "串并联图",
  "stack": "栈",
  "shortest-path": "最短路",
  "sign-assignment": "符号分配",
  "small-to-large": "小并大",
  "sorting": "排序",
  "splay-tree": "伸展树",
  "sparse-candidate-edges": "稀疏候选边",
  "sparse-exception-updates": "稀疏例外更新",
  "sparse-table": "Sparse Table",
  "sqrt-decomposition": "分块",
  "sos-dp": "SOS DP",
  "sprague-grundy": "Sprague-Grundy",
  "state-augmentation": "状态增强",
  "state-compression": "状态压缩",
  "state-dominance": "状态支配",
  "stirling-number": "Stirling 数",
  "string": "字符串",
  "submask-supermask": "子掩码/超掩码",
  "sum-xor-identity": "和异或恒等式",
  "suffix-array": "后缀数组",
  "subset-dp": "子集 DP",
  "subset-counting": "子集计数",
  "suffix-structures": "后缀结构",
  "subset-convolution": "子集卷积",
  "sweep-line": "扫描线",
  "symmetric-pairing": "对称配对",
  "tangent": "切线",
  "symmetry": "对称性",
  "ternary-search": "三分",
  "tight-loose-state": "紧/松状态",
  "tiling": "平铺构造",
  "top-k-maintenance": "Top-K 维护",
  "topological-sort": "拓扑排序",
  "transform": "变换",
  "transposition-principle": "转置原理",
  "tree": "树",
  "tree-centroid": "树重心",
  "tree-diameter": "树直径",
  "tree-dp": "树形 DP",
  "tree-dfs": "树上 DFS",
  "tree-hashing": "树哈希",
  "tree-matching": "树匹配",
  "trie": "字典树",
  "trick": "技巧",
  "two-pointers": "双指针",
  "versioned-node": "版本节点",
  "weighted-lower-bound": "加权下界",
  "xor-interval-decomposition": "异或区间分解",
  "xor-hashing": "异或哈希",
  "wavelet-matrix": "小波矩阵",
  "xor-basis": "异或线性基",
  "xor-pair-counting": "异或差数对计数",
  "xor-vector-space": "异或向量空间",
  "xor-subset": "异或子集",
  "z-function": "Z 函数"
};

export function readStoredLocale(): Locale {
  if (typeof window === "undefined") return DEFAULT_LOCALE;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === "en" || stored === "zh" ? stored : DEFAULT_LOCALE;
}

export function writeStoredLocale(locale: Locale): void {
  window.localStorage.setItem(STORAGE_KEY, locale);
}

export function ui(locale: Locale, key: UiKey): string {
  return UI_TEXT[locale][key];
}

export function importanceLabel(locale: Locale, importance: Importance): string {
  return IMPORTANCE_TEXT[locale][importance];
}

export function ratingStatusLabel(locale: Locale, status: RatingStatus): string {
  return RATING_STATUS_TEXT[locale][status];
}

export function valueLabel(locale: Locale, value: string): string {
  const normalized = value.toLowerCase().replace(/ /g, "-").replace(/_/g, "-");
  return GENERIC_VALUE_TEXT[locale][value] ?? GENERIC_VALUE_TEXT[locale][normalized] ?? prettifyToken(value);
}

export function tagLabel(locale: Locale, tag: string, mode: "leaf" | "path" = "leaf"): string {
  if (locale === "en") {
    return mode === "leaf" ? prettifyToken(lastSegment(tag)) : tag;
  }

  const exact = (FULL_TAG_TEXT_ZH as Record<string, string>)[tag];
  if (exact) return exact;

  const segments = tag.split("/");
  if (mode === "leaf") {
    return SEGMENT_TEXT_ZH[lastSegment(tag)] ?? prettifyToken(lastSegment(tag));
  }
  return segments
    .map((segment) => SEGMENT_TEXT_ZH[segment] ?? prettifyToken(segment))
    .join(" / ");
}

export function ratingText(
  locale: Locale,
  rating: number | null,
  status: RatingStatus
): string {
  if (rating === null || status !== "official") return ratingStatusLabel(locale, status);
  return String(rating);
}

export function statsText(locale: Locale, stats: Stats): string {
  if (locale === "zh") {
    return `${stats.canonical_problems} 道题 / ${stats.tags} 个标签 / ${stats.favorites} 个收藏`;
  }
  return `${stats.canonical_problems} problems / ${stats.tags} tags / ${stats.favorites} favorites`;
}

export function shownText(locale: Locale, count: number): string {
  return locale === "zh" ? `显示 ${count} 道` : `${count} shown`;
}

function lastSegment(tag: string): string {
  return tag.split("/").slice(-1)[0] ?? tag;
}

function prettifyToken(value: string): string {
  return value.replace(/[-_]/g, " ");
}
