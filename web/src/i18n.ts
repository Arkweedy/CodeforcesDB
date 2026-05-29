import type { Importance, RatingStatus, Stats } from "./types";

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
    accepted_submission: "通过提交",
    "auto-seeded": "自动种子",
    auto_seeded: "自动种子",
    blog: "博客",
    candidate: "候选",
    cfstep_hints: "CFStep 提示",
    "div1-div2-overlap": "Div.1/Div.2 重题",
    editorial: "题解",
    excluded: "已排除",
    high: "高",
    "luogu-solution": "洛谷题解",
    luogu_solution: "洛谷题解",
    low: "低",
    main: "主解法",
    medium: "中",
    needs_manual_review: "需要人工复核",
    reviewed: "已复核",
    secondary: "次解法",
    statement: "题面"
  },
  en: {
    "accepted-code": "Accepted code",
    accepted_submission: "Accepted submission",
    "auto-seeded": "Auto seeded",
    auto_seeded: "Auto seeded",
    blog: "Blog",
    candidate: "Candidate",
    cfstep_hints: "CFStep hints",
    "div1-div2-overlap": "Div.1/Div.2 overlap",
    editorial: "Editorial",
    excluded: "Excluded",
    high: "High",
    "luogu-solution": "Luogu solutions",
    luogu_solution: "Luogu solutions",
    low: "Low",
    main: "Main",
    medium: "Medium",
    needs_manual_review: "Needs manual review",
    reviewed: "Reviewed",
    secondary: "Secondary",
    statement: "Statement"
  }
};

const FULL_TAG_TEXT_ZH: Record<string, string> = {
  "algorithm": "算法",
  "algorithm/binary-lifting": "倍增",
  "algorithm/bitmask": "位掩码",
  "algorithm/bitmask/bitwise-greedy": "按位贪心",
  "algorithm/bitmask/lowbit": "Lowbit",
  "algorithm/bitmask/xor-subset": "异或子集",
  "algorithm/divide-and-conquer": "分治",
  "algorithm/divide-and-conquer/cartesian-tree": "笛卡尔树",
  "dp": "动态规划",
  "dp/automaton-dp": "自动机 DP",
  "dp/aliens-trick": "Aliens Trick",
  "dp/bitmask-dp": "状压 DP",
  "dp/bitset-dp": "Bitset DP",
  "dp/bracket-dp": "括号结构 DP",
  "dp/counting-dp": "计数 DP",
  "dp/convex-hull-optimization": "斜率优化 DP",
  "dp/decision-monotonicity": "决策单调性优化",
  "dp/digit-dp": "数位 DP",
  "dp/finite-state-dp": "有限状态 DP",
  "dp/graph-dp": "图上 DP",
  "dp/grid-dp": "网格 DP",
  "dp/interval-dp": "区间 DP",
  "dp/knapsack-dp": "背包 DP",
  "dp/lis-dp": "LIS/非降子序列 DP",
  "dp/max-subarray": "最大子段和 DP",
  "dp/pair-dp": "二元组 DP",
  "dp/prefix-max-optimization": "前缀最大值优化",
  "dp/probability-dp": "概率 DP",
  "dp/residue-knapsack": "同余背包",
  "dp/rerooting-dp": "换根 DP",
  "dp/prefix-sum-optimization": "前缀和优化",
  "dp/subset-dp": "子集 DP",
  "dp/tree-dp": "树形 DP",
  "graph": "图论",
  "graph/2-sat": "2-SAT",
  "graph/bipartite-graph": "二分图",
  "graph/bottleneck-path": "瓶颈路径",
  "graph/bfs": "BFS",
  "graph/bridge": "桥",
  "graph/cactus": "仙人掌",
  "graph/centroid-decomposition": "点分治",
  "graph/chain-graph": "链图",
  "graph/connectivity": "连通性",
  "graph/cycle-space": "环空间",
  "graph/dag": "DAG",
  "graph/degree-sequence": "度数序列",
  "graph/planar-graph": "平面图",
  "graph/dfs": "DFS",
  "graph/dfs-order": "DFS 序",
  "graph/euler-trail": "欧拉路径",
  "graph/euler-tour": "欧拉序",
  "graph/edge-orientation": "边定向",
  "graph/flow": "网络流",
  "graph/functional-graph": "函数图",
  "graph/grid-separator": "网格分隔链",
  "graph/heavy-light-decomposition": "树链剖分",
  "graph/layered-graph": "分层图",
  "graph/lca": "最近公共祖先",
  "graph/line-graph": "线图",
  "graph/matching": "匹配",
  "graph/mst": "最小生成树",
  "graph/path-counting": "路径计数",
  "graph/series-parallel-graph": "串并联图",
  "graph/shortest-path": "最短路",
  "graph/tree": "树",
  "graph/tree-centroid": "树重心",
  "graph/tree-diameter": "树直径",
  "graph/tree-dfs": "树上 DFS",
  "graph/tree-hashing": "树哈希",
  "graph/transitive-reduction": "传递约简",
  "graph/virtual-tree": "虚树",
  "algorithm/hashing": "哈希",
  "algorithm/majority-vote": "多数投票",
  "algorithm/majority-vote/misra-gries": "Misra-Gries 多数投票",
  "algorithm/search/meet-in-the-middle": "折半搜索",
  "algorithm/prefix-sums": "前缀和",
  "algorithm/prefix-xor": "前缀异或",
  "algorithm/search": "搜索",
  "algorithm/search/binary-search": "二分",
  "algorithm/search/ternary-search": "三分",
  "algorithm/sorting": "排序",
  "algorithm/sqrt-decomposition": "分块",
  "string": "字符串",
  "string/acam": "AC 自动机",
  "string/border": "Border",
  "string/bracket-sequence": "括号序列",
  "string/finite-automaton": "有限自动机",
  "string/formal-grammar": "形式文法",
  "string/kmp-prefix-function": "KMP 前缀函数",
  "string/run-length-encoding": "游程编码",
  "string/suffix-array": "后缀数组",
  "string/suffix-structures": "后缀结构",
  "math/transform": "变换",
  "math/transform/convolution": "卷积",
  "math/transform/fft": "FFT",
  "math/transform/fwt": "FWT",
  "math/transform/fwt/and-fwt": "AND FWT",
  "algorithm/two-pointers": "双指针",
  "paradigm/communication": "通信",
  "data-structure": "数据结构",
  "data-structure/difference-array": "差分数组",
  "data-structure/dsu": "并查集",
  "data-structure/dsu/next-pointer": "next 指针并查集",
  "data-structure/dsu/rollback": "可回滚并查集",
  "data-structure/dsu/small-to-large": "并查集小并大",
  "data-structure/dsu/versioned-node": "版本节点并查集",
  "data-structure/trie": "字典树",
  "data-structure/fenwick-tree": "树状数组",
  "data-structure/hash-map": "哈希表",
  "data-structure/implicit-sequence": "隐式序列",
  "data-structure/lazy-propagation": "懒标记",
  "data-structure/li-chao-tree": "李超线段树",
  "data-structure/monotonic-stack": "单调栈",
  "data-structure/ordered-multiset": "有序可重集",
  "data-structure/order-statistics-tree": "顺序统计树",
  "data-structure/priority-queue": "优先队列",
  "data-structure/persistent-balanced-tree": "可持久化平衡树",
  "data-structure/persistent-segment-tree": "可持久化线段树",
  "data-structure/queue": "队列",
  "data-structure/segment-tree": "线段树",
  "data-structure/sparse-table": "Sparse Table",
  "data-structure/stack": "栈",
  "data-structure/wavelet-matrix": "小波矩阵",
  "implementation": "实现",
  "implementation/parsing": "解析",
  "implementation/parsing/expression": "表达式解析",
  "math": "数学",
  "math/combinatorics": "组合数学",
  "math/combinatorics/binomial-basis": "二项式基",
  "math/combinatorics/binomial-identity": "二项式恒等式",
  "math/combinatorics/catalan": "Catalan 数",
  "math/combinatorics/eulerian-number": "欧拉数",
  "math/combinatorics/multinomial": "多项式系数",
  "math/combinatorics/permutation-counting": "排列计数",
  "math/combinatorics/prufer-sequence": "Prüfer 序列",
  "math/combinatorics/subset-counting": "子集计数",
  "math/game-theory": "博弈论",
  "math/game-theory/minimax": "Minimax",
  "math/game-theory/sprague-grundy": "Sprague-Grundy",
  "math/generating-function": "生成函数",
  "math/generating-function/egf": "指数生成函数",
  "math/geometry": "几何",
  "math/geometry/convexity": "凸性",
  "math/geometry/convex-hull": "凸包",
  "math/geometry/convex-layers": "凸包层",
  "math/geometry/projection-metric": "投影度量",
  "math/geometry/tangent": "切线",
  "math/inclusion-exclusion": "容斥",
  "math/inclusion-exclusion/minmax": "Min-Max 容斥",
  "math/inequality": "不等式",
  "math/information-theory": "信息论",
  "math/information-theory/entropy": "熵",
  "math/identity": "代数恒等式",
  "math/linear-algebra": "线性代数",
  "math/linear-algebra/determinant": "行列式",
  "math/linear-algebra/linear-system": "线性方程组",
  "math/linear-algebra/matrix": "矩阵",
  "math/linear-algebra/matrix-exponentiation": "矩阵快速幂",
  "math/linear-algebra/xor-basis": "异或线性基",
  "math/linear-algebra/xor-vector-space": "异或向量空间",
  "math/mex": "MEX",
  "math/number-theory": "数论",
  "math/number-theory/chinese-remainder-theorem": "中国剩余定理",
  "math/number-theory/divisibility": "整除",
  "math/number-theory/divisor-sieve": "因子筛",
  "math/number-theory/gcd": "GCD",
  "math/number-theory/gcd-convolution": "GCD 卷积",
  "math/number-theory/lcm": "LCM",
  "math/number-theory/mobius-inversion": "莫比乌斯反演",
  "math/number-theory/modular-arithmetic": "模运算",
  "math/number-theory/multiplicative-order": "乘法阶",
  "math/number-theory/mobius": "莫比乌斯",
  "math/number-theory/prime-factor-count": "质因子计数",
  "math/probability": "概率",
  "math/probability/bayesian-update": "贝叶斯更新",
  "math/probability/expected-progress": "期望推进",
  "math/probability/linearity-of-expectation": "期望线性性",
  "paradigm": "范式",
  "paradigm/brute-force": "暴力",
  "paradigm/constructive": "构造",
  "paradigm/greedy": "贪心",
  "paradigm/interactive": "交互",
  "paradigm/interactive/oracle-reconstruction": "交互式重构",
  "paradigm/offline": "离线",
  "paradigm/online": "在线",
  "paradigm/sweep-line": "扫描线",
  "special": "特殊题型",
  "trick/scheduling": "调度",
  "trick": "技巧",
  "trick/amortized-delete-once": "均摊一次删除",
  "trick/batch-simulation": "批量模拟",
  "trick/back-edge-enumeration": "返祖边枚举",
  "trick/binary-carry": "二进制进位",
  "trick/canonical-form": "规范形",
  "trick/case-analysis": "分类讨论",
  "trick/circular-interval": "环形区间",
  "trick/classify-overlap": "重叠分类",
  "trick/component-decomposition": "分量分解",
  "trick/complement-symmetry": "补集对称",
  "trick/common-prefix-cancellation": "公共前缀消去",
  "trick/convert-to-prefix": "转为前缀",
  "trick/cycle-detection": "判环",
  "trick/decision-tree": "决策树",
  "trick/difference-transform": "差分转化",
  "trick/distance-signature": "距离签名",
  "trick/dfs-order-rectangle": "DFS 序矩形化",
  "trick/extreme-position": "极端位置",
  "trick/group-by-divisor": "按因子分组",
  "trick/group-by-coordinate": "按坐标分组",
  "trick/group-by-diagonal": "按对角线分组",
  "trick/harmonic-sum": "调和级数枚举",
  "trick/handle-special-case": "特判处理",
  "trick/helper-buffer": "辅助缓冲",
  "trick/highest-differing-bit": "最高不同位",
  "trick/interval-feasibility": "区间可行性",
  "trick/invariant": "不变量",
  "trick/linear-objective-extreme-choice": "线性目标取端点",
  "trick/lazy-affine-update": "懒惰仿射更新",
  "trick/lazy-deletion": "懒删除",
  "trick/laminar-family": "嵌套集合族",
  "trick/layer-counting": "按层统计",
  "trick/lexicographic-order": "字典序",
  "trick/maintain-contribution": "维护贡献",
  "trick/mark-multiples": "标记倍数",
  "trick/monotonicity": "单调性",
  "trick/non-overlap": "不重叠选择",
  "trick/one-parameter-optimization": "单参数优化",
  "trick/median-threshold": "中位数阈值",
  "trick/permutation-structure": "排列结构",
  "trick/parity": "奇偶性",
  "trick/periodicity": "周期性",
  "trick/pigeonhole-principle": "鸽巢原理",
  "trick/popcount-invariant": "popcount 不变量",
  "trick/prefix-suffix-extrema": "前后缀极值",
  "trick/quotient-state-space": "商状态空间",
  "trick/query-differencing": "查询差分",
  "trick/recursive-construction": "递归构造",
  "trick/residue-class-decomposition": "剩余类分解",
  "trick/reverse-process": "逆向处理",
  "trick/sign-assignment": "符号分配",
  "trick/state-augmentation": "状态增强",
  "trick/state-compression": "状态压缩",
  "trick/sum-xor-identity": "和异或恒等式",
  "trick/symmetry": "对称性",
  "trick/tight-loose-state": "紧/松状态",
  "trick/tiling": "平铺构造",
  "trick/xor-interval-decomposition": "异或区间分解",
  "trick/xor-hashing": "异或哈希"
};

const SEGMENT_TEXT_ZH: Record<string, string> = {
  "2-sat": "2-SAT",
  "acam": "AC 自动机",
  "algorithm": "算法",
  "automaton-dp": "自动机 DP",
  "batch-simulation": "批量模拟",
  "back-edge-enumeration": "返祖边枚举",
  "bayesian-update": "贝叶斯更新",
  "bfs": "BFS",
  "binary-lifting": "倍增",
  "binary-search": "二分",
  "binary-carry": "二进制进位",
  "binomial-identity": "二项式恒等式",
  "bipartite-graph": "二分图",
  "bitmask": "位掩码",
  "bitmask-dp": "状压 DP",
  "bitwise-greedy": "按位贪心",
  "border": "Border",
  "bridge": "桥",
  "brute-force": "暴力",
  "bottleneck-path": "瓶颈路径",
  "cartesian-tree": "笛卡尔树",
  "canonical-form": "规范形",
  "case-analysis": "分类讨论",
  "cactus": "仙人掌",
  "catalan": "Catalan 数",
  "centroid-decomposition": "点分治",
  "chain-graph": "链图",
  "chinese-remainder-theorem": "中国剩余定理",
  "circular-interval": "环形区间",
  "classify-overlap": "重叠分类",
  "combinatorics": "组合数学",
  "component-decomposition": "分量分解",
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
  "data-structure": "数据结构",
  "dag": "DAG",
  "decision-tree": "决策树",
  "degree-sequence": "度数序列",
  "difference-array": "差分数组",
  "dfs": "DFS",
  "dfs-order": "DFS 序",
  "digit-dp": "数位 DP",
  "difference-transform": "差分转化",
  "distance-signature": "距离签名",
  "divide-and-conquer": "分治",
  "divisibility": "整除",
  "divisor-sieve": "因子筛",
  "dp": "动态规划",
  "dsu": "并查集",
  "egf": "指数生成函数",
  "entropy": "熵",
  "eulerian-number": "欧拉数",
  "expected-progress": "期望推进",
  "expression": "表达式",
  "extreme-position": "极端位置",
  "euler-trail": "欧拉路径",
  "euler-tour": "欧拉序",
  "edge-orientation": "边定向",
  "fenwick-tree": "树状数组",
  "finite-state-dp": "有限状态 DP",
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
  "grid-dp": "网格 DP",
  "group-by-divisor": "按因子分组",
  "handle-special-case": "特判",
  "hash-map": "哈希表",
  "hashing": "哈希",
  "harmonic-sum": "调和级数枚举",
  "heavy-light-decomposition": "树链剖分",
  "helper-buffer": "辅助缓冲",
  "highest-differing-bit": "最高不同位",
  "implementation": "实现",
  "implicit-sequence": "隐式序列",
  "inclusion-exclusion": "容斥",
  "interactive": "交互",
  "invariant": "不变量",
  "inequality": "不等式",
  "information-theory": "信息论",
  "interval-feasibility": "区间可行性",
  "kmp-prefix-function": "KMP 前缀函数",
  "knapsack-dp": "背包 DP",
  "layered-graph": "分层图",
  "lexicographic-order": "字典序",
  "lca": "最近公共祖先",
  "line-graph": "线图",
  "lazy-affine-update": "懒惰仿射更新",
  "lazy-deletion": "懒删除",
  "lazy-propagation": "懒标记",
  "li-chao-tree": "李超线段树",
  "linear-algebra": "线性代数",
  "linear-system": "线性方程组",
  "linear-objective-extreme-choice": "线性目标取端点",
  "linearity-of-expectation": "期望线性性",
  "lis-dp": "LIS/非降子序列 DP",
  "lowbit": "Lowbit",
  "maintain-contribution": "维护贡献",
  "mark-multiples": "标记倍数",
  "matching": "匹配",
  "math": "数学",
  "matrix": "矩阵",
  "matrix-exponentiation": "矩阵快速幂",
  "majority-vote": "多数投票",
  "max-subarray": "最大子段和",
  "modular-arithmetic": "模运算",
  "meet-in-the-middle": "折半搜索",
  "median-threshold": "中位数阈值",
  "misra-gries": "Misra-Gries",
  "minmax": "Min-Max",
  "minimax": "Minimax",
  "mobius": "莫比乌斯",
  "mobius-inversion": "莫比乌斯反演",
  "monotonic-stack": "单调栈",
  "monotonicity": "单调性",
  "mst": "最小生成树",
  "multinomial": "多项式系数",
  "multiplicative-order": "乘法阶",
  "next-pointer": "next 指针",
  "non-overlap": "不重叠选择",
  "number-theory": "数论",
  "offline": "离线",
  "online": "在线",
  "one-parameter-optimization": "单参数优化",
  "ordered-multiset": "有序可重集",
  "order-statistics-tree": "顺序统计树",
  "paradigm": "范式",
  "parity": "奇偶性",
  "parsing": "解析",
  "path-counting": "路径计数",
  "permutation-counting": "排列计数",
  "permutation-structure": "排列结构",
  "periodicity": "周期性",
  "pigeonhole-principle": "鸽巢原理",
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
  "probability": "概率",
  "prufer-sequence": "Prüfer 序列",
  "queue": "队列",
  "quotient-state-space": "商状态空间",
  "query-differencing": "查询差分",
  "residue-knapsack": "同余背包",
  "run-length-encoding": "游程编码",
  "rollback": "可回滚",
  "reverse-process": "逆向处理",
  "scheduling": "调度",
  "search": "搜索",
  "segment-tree": "线段树",
  "series-parallel-graph": "串并联图",
  "stack": "栈",
  "shortest-path": "最短路",
  "sign-assignment": "符号分配",
  "small-to-large": "小并大",
  "sorting": "排序",
  "sparse-table": "Sparse Table",
  "sqrt-decomposition": "分块",
  "sprague-grundy": "Sprague-Grundy",
  "state-augmentation": "状态增强",
  "state-compression": "状态压缩",
  "string": "字符串",
  "sum-xor-identity": "和异或恒等式",
  "suffix-array": "后缀数组",
  "subset-dp": "子集 DP",
  "subset-counting": "子集计数",
  "suffix-structures": "后缀结构",
  "sweep-line": "扫描线",
  "tangent": "切线",
  "symmetry": "对称性",
  "ternary-search": "三分",
  "tight-loose-state": "紧/松状态",
  "tiling": "平铺构造",
  "transform": "变换",
  "tree": "树",
  "tree-centroid": "树重心",
  "tree-diameter": "树直径",
  "tree-dp": "树形 DP",
  "tree-dfs": "树上 DFS",
  "tree-hashing": "树哈希",
  "trie": "字典树",
  "trick": "技巧",
  "two-pointers": "双指针",
  "versioned-node": "版本节点",
  "xor-interval-decomposition": "异或区间分解",
  "xor-hashing": "异或哈希",
  "wavelet-matrix": "小波矩阵",
  "xor-basis": "异或线性基",
  "xor-vector-space": "异或向量空间",
  "xor-subset": "异或子集"
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

  const exact = FULL_TAG_TEXT_ZH[tag];
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
