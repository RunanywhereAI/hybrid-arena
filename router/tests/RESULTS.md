# Router test results

Run at 2026-04-26T08:00:56.609Z

Proxy: http://127.0.0.1:8787  
Local backend: http://127.0.0.1:11434/v1 model=qwen3-coder:30b reachable=true  
Cloud backend: https://api.openai.com/v1 model=gpt-5.5 reachable=true key_present=true  
Cloud sample models: gpt-4-0613, gpt-4, gpt-3.5-turbo, gpt-5.5-pro-2026-04-23, gpt-image-2-2026-04-21, gpt-5.5, gpt-5.5-2026-04-23, gpt-5.5-pro  

## Decision matrix (which backend each strategy chose)

| prompt | always-local | always-cloud | rules | heuristic | llm-classifier | embedding-knn | cascade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **trivial-rename** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-typo** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-fib** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-comment** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-py-question** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-loop** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-format** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **trivial-async** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **moderate-test** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **moderate-bugfix** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | ☁ cloud | 🖥 local |
| **complex-design** | 🖥 local | ☁ cloud | ☁ cloud | ☁ cloud | ☁ cloud | ☁ cloud | ☁ cloud |
| **complex-refactor** | 🖥 local | ☁ cloud | ☁ cloud | ☁ cloud | ☁ cloud | ☁ cloud | ☁ cloud |
| **complex-perf** | 🖥 local | ☁ cloud | ☁ cloud | 🖥 local | 🖥 local | ☁ cloud | 🖥 local |
| **complex-architecture** | 🖥 local | ☁ cloud | ☁ cloud | ☁ cloud | 🖥 local | ☁ cloud | ☁ cloud |
| **long-context** | 🖥 local | ☁ cloud | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local |
| **ambiguous-short** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | ☁ cloud | 🖥 local |
| **tools-heavy** | 🖥 local | ☁ cloud | 🖥 local | 🖥 local | 🖥 local | 🖥 local | 🖥 local |

## Latency per strategy (median ms)

- **always-local**: median 2.9s, min 215ms, max 8.7s, n=17
- **always-cloud**: median 2.6s, min 1.3s, max 17.1s, n=17
- **rules**: median 2.6s, min 186ms, max 16.3s, n=17
- **heuristic**: median 2.4s, min 139ms, max 15.0s, n=17
- **llm-classifier**: median 3.5s, min 213ms, max 15.4s, n=17
- **embedding-knn**: median 2.6s, min 175ms, max 15.3s, n=17
- **cascade**: median 2.5s, min 127ms, max 16.7s, n=17

## Per-prompt detail

### trivial-rename

> Rename the variable `total` to `subtotal` in this snippet:  ```js function price(items) {   let total = 0;   for (const i of items) total += i.price;   return total; } ```

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 666ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.6s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 528ms | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.85 / rules: kw[local]: rename |
| heuristic | local | qwen3-coder:30b | 416ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=-11.5 >=25? → local] uTok=43(+0.5) cb=1(+6) -local-kw=1(-18) |
| llm-classifier | local | qwen3-coder:30b | 10.7s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (10240ms) |
| embedding-knn | local | qwen3-coder:30b | 1.7s | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=1.00 / embedding-knn[k=5]: cloud=0/5 (w=0.00 vs 3.06) (1341ms) — top: "Rename the variable foo to bar in src/utils.ts" |
| cascade | local | qwen3-coder:30b | 391ms | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=36.5]: heuristic[score=-11.5 >=25? → local] uTok=43(+0.5) cb=1(+6) -local-kw=1(-18) |

<details><summary>heuristic-routed response excerpt</summary>

```
```js function price(items) { let subtotal = 0; for (const i of items) subtotal += i.price; return subtotal; } ```
```

</details>

### trivial-typo

> Fix the typo: `parseRequst` should be `parseRequest`. Show only the renamed function header.

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 215ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.2s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 186ms | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.85 / rules: kw[local]: rename,typo,fix the typo |
| heuristic | local | qwen3-coder:30b | 139ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=-53.7 >=25? → local] uTok=23(+0.3) -local-kw=3(-54) |
| llm-classifier | local | qwen3-coder:30b | 213ms | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (87ms) |
| embedding-knn | local | qwen3-coder:30b | 175ms | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=0.63 / embedding-knn[k=5]: cloud=2/5 (w=1.23 vs 2.10) (35ms) — top: "Fix the typo in this function name: parseRequst → parseReque" |
| cascade | local | qwen3-coder:30b | 127ms | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=78.7]: heuristic[score=-53.7 >=25? → local] uTok=23(+0.3) -local-kw=3(-54) |

<details><summary>heuristic-routed response excerpt</summary>

```
```c parseRequest ```
```

</details>

### trivial-fib

> Write a one-line JavaScript function fib(n) returning the nth Fibonacci number (n>=0).

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 514ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.2s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 520ms | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=22, codeBlocks=0) |
| heuristic | local | qwen3-coder:30b | 445ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.99 / heuristic[score=0.3 >=25? → local] uTok=22(+0.3) |
| llm-classifier | local | qwen3-coder:30b | 661ms | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (206ms) |
| embedding-knn | local | qwen3-coder:30b | 477ms | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=1.00 / embedding-knn[k=5]: cloud=0/5 (w=0.00 vs 2.85) (18ms) — top: "Write a one-line function that returns the Fibonacci sequenc" |
| cascade | local | qwen3-coder:30b | 457ms | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.99 / cascade[trust-heuristic dist=24.7]: heuristic[score=0.3 >=25? → local] uTok=22(+0.3) |

<details><summary>heuristic-routed response excerpt</summary>

```
```javascript const fib = (n, a = 0, b = 1) => n === 0 ? a : fib(n - 1, b, a + b); ```
```

</details>

### trivial-comment

> Add a JSDoc comment to:  ```js function formatDate(d) { return d.toISOString().slice(0, 10); } ```

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 997ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.1s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 971ms | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.85 / rules: kw[local]: format |
| heuristic | local | qwen3-coder:30b | 892ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=-11.7 >=25? → local] uTok=25(+0.3) cb=1(+6) -local-kw=1(-18) |
| llm-classifier | local | qwen3-coder:30b | 987ms | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (110ms) |
| embedding-knn | local | qwen3-coder:30b | 929ms | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=1.00 / embedding-knn[k=5]: cloud=0/5 (w=0.00 vs 3.27) (39ms) — top: "Add a JSDoc comment to the formatDate function" |
| cascade | local | qwen3-coder:30b | 886ms | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=36.7]: heuristic[score=-11.7 >=25? → local] uTok=25(+0.3) cb=1(+6) -local-kw=1(-18) |

<details><summary>heuristic-routed response excerpt</summary>

```
```js /** * Formats a Date object into an ISO date string (YYYY-MM-DD format). * @param {Date} d - The Date object to format * @returns {string} The date in YYYY-MM-DD format (e.g., "2023-12-25") */ function formatDate(d) { return d.toISOSt
```

</details>

### trivial-py-question

> Quick: what is the syntax for a Python dict comprehension that maps name → length over a list of strings?

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 493ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 1.8s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 496ms | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.85 / rules: kw[local]: what is,quick |
| heuristic | local | qwen3-coder:30b | 427ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=-35.7 >=25? → local] uTok=27(+0.3) -local-kw=2(-36) |
| llm-classifier | local | qwen3-coder:30b | 616ms | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (74ms) |
| embedding-knn | local | qwen3-coder:30b | 449ms | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=1.00 / embedding-knn[k=5]: cloud=0/5 (w=0.00 vs 3.15) (25ms) — top: "What is the syntax for a Python dict comprehension?" |
| cascade | local | qwen3-coder:30b | 423ms | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=60.7]: heuristic[score=-35.7 >=25? → local] uTok=27(+0.3) -local-kw=2(-36) |

<details><summary>heuristic-routed response excerpt</summary>

```
```python {name: len(name) for name in names} ``` Where `names` is your list of strings. This creates a dictionary mapping each string to its length.
```

</details>

### trivial-loop

> Convert this for loop to a .map():  for (const x of arr) result.push(x*2)

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 2.0s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.1s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 1.8s | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.85 / rules: kw[local]: convert |
| heuristic | local | qwen3-coder:30b | 2.0s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=-17.8 >=25? → local] uTok=19(+0.2) -local-kw=1(-18) |
| llm-classifier | local | qwen3-coder:30b | 1.9s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (92ms) |
| embedding-knn | local | qwen3-coder:30b | 1.8s | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=1.00 / embedding-knn[k=5]: cloud=0/5 (w=0.00 vs 3.12) (24ms) — top: "Convert this for loop to a map: for (const x of arr) result." |
| cascade | local | qwen3-coder:30b | 1.9s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=42.8]: heuristic[score=-17.8 >=25? → local] uTok=19(+0.2) -local-kw=1(-18) |

<details><summary>heuristic-routed response excerpt</summary>

```
Here's how to convert that for loop to use `.map()`: ```javascript const result = arr.map(x => x * 2); ``` The `.map()` method creates a new array by applying a function to each element of the original array. In this case, it multiplies eac
```

</details>

### trivial-format

> Add a missing semicolon at the end of `let x = 1`

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 241ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 1.6s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 218ms | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=13, codeBlocks=0) |
| heuristic | local | qwen3-coder:30b | 186ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=0.2 >=25? → local] uTok=13(+0.2) |
| llm-classifier | local | qwen3-coder:30b | 234ms | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (73ms) |
| embedding-knn | local | qwen3-coder:30b | 212ms | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=1.00 / embedding-knn[k=5]: cloud=0/5 (w=0.00 vs 3.12) (52ms) — top: "Add a missing semicolon" |
| cascade | local | qwen3-coder:30b | 161ms | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=24.8]: heuristic[score=0.2 >=25? → local] uTok=13(+0.2) |

<details><summary>heuristic-routed response excerpt</summary>

```
```javascript let x = 1; ```
```

</details>

### trivial-async

> Make this function async and return a resolved Promise of 42:  ```js function get42() { return 42; } ```

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 2.9s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 1.3s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 2.6s | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=26, codeBlocks=1) |
| heuristic | local | qwen3-coder:30b | 2.4s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.87 / heuristic[score=6.3 >=25? → local] uTok=26(+0.3) cb=1(+6) |
| llm-classifier | local | qwen3-coder:30b | 2.9s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (126ms) |
| embedding-knn | local | qwen3-coder:30b | 1.9s | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=0.62 / embedding-knn[k=5]: cloud=2/5 (w=1.18 vs 1.90) (35ms) — top: "Make this function async" |
| cascade | local | qwen3-coder:30b | 2.5s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.87 / cascade[trust-heuristic dist=18.7]: heuristic[score=6.3 >=25? → local] uTok=26(+0.3) cb=1(+6) |

<details><summary>heuristic-routed response excerpt</summary>

```
Here are a few ways to make the function async and return a resolved Promise of 42: **Option 1: Using `async` keyword with `return`** ```js async function get42() { return 42; } ``` **Option 2: Using `async` keyword with `Promise.resolve()`
```

</details>

### moderate-test

> Write a Jest unit test for this function that covers empty input, one element, and a typical case:  ```js export function uniq(arr) { return [...new Set(arr)]; } ```

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 3.8s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.6s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 3.7s | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=42, codeBlocks=1) |
| heuristic | local | qwen3-coder:30b | 3.4s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.87 / heuristic[score=6.5 >=25? → local] uTok=42(+0.5) cb=1(+6) |
| llm-classifier | local | qwen3-coder:30b | 3.5s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (104ms) |
| embedding-knn | local | qwen3-coder:30b | 3.7s | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=0.81 / embedding-knn[k=5]: cloud=1/5 (w=0.61 vs 2.58) (26ms) — top: "Run the tests for this file" |
| cascade | local | qwen3-coder:30b | 3.7s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.87 / cascade[trust-heuristic dist=18.5]: heuristic[score=6.5 >=25? → local] uTok=42(+0.5) cb=1(+6) |

<details><summary>heuristic-routed response excerpt</summary>

```
Here's a Jest unit test for the `uniq` function that covers all the specified cases: ```js import { uniq } from './your-module-file'; // Adjust the import path as needed describe('uniq function', () => { test('should handle empty input', ()
```

</details>

### moderate-bugfix

> This binary search has an off-by-one bug. Find it and fix it:  ```js function bs(arr, target) {   let lo = 0, hi = arr.length;   while (lo < hi) {     const mid = (lo + hi) >> 1;     if (arr[mid] === …

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 4.0s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 6.1s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 3.0s | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=75, codeBlocks=1) |
| heuristic | local | qwen3-coder:30b | 3.9s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.86 / heuristic[score=6.9 >=25? → local] uTok=75(+0.9) cb=1(+6) |
| llm-classifier | local | qwen3-coder:30b | 3.9s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (102ms) |
| embedding-knn | cloud | gpt-5.5 | 4.7s | [router] strategy=embedding-knn → CLOUD (gpt-5.5) / conf=0.59 / embedding-knn[k=5]: cloud=3/5 (w=1.76 vs 1.24) (99ms) — top: "Convert this for loop to a map: for (const x of arr) result." |
| cascade | local | qwen3-coder:30b | 4.0s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.86 / cascade[trust-heuristic dist=18.1]: heuristic[score=6.9 >=25? → local] uTok=75(+0.9) cb=1(+6) |

<details><summary>heuristic-routed response excerpt</summary>

```
Looking at this binary search implementation, I can identify the off-by-one bug in the update logic. The issue is in these lines: ```js if (arr[mid] < target) lo = mid; // BUG: should be lo = mid + 1 else hi = mid; // BUG: should be hi = mi
```

</details>

### complex-design

> Design a multi-tenant authentication system with row-level security in Postgres. Walk me through the schema, the JWT structure, edge cases like impersonation and tenant migration, and what to log. Be …

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 7.9s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 13.6s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | cloud | gpt-5.5 | 16.3s | [router] strategy=rules → CLOUD (gpt-5.5) / conf=0.65 / rules: kw[cloud]: design,long,comprehensive |
| heuristic | cloud | gpt-5.5 | 15.0s | [router] strategy=heuristic → CLOUD (gpt-5.5) / conf=1.00 / heuristic[score=56.8 >=25? → cloud] uTok=63(+0.8) kw=4(+56) |
| llm-classifier | cloud | gpt-5.5 | 15.4s | [router] strategy=llm-classifier → CLOUD (gpt-5.5) / conf=0.80 / llm-classifier(qwen3:0.6b): "COMPLEX" (357ms) |
| embedding-knn | cloud | gpt-5.5 | 15.3s | [router] strategy=embedding-knn → CLOUD (gpt-5.5) / conf=1.00 / embedding-knn[k=5]: cloud=5/5 (w=3.49 vs 0.00) (262ms) — top: "Design a multi-tenant authentication system with row-level s" |
| cascade | cloud | gpt-5.5 | 16.7s | [router] strategy=cascade → CLOUD (gpt-5.5) / conf=1.00 / cascade[trust-heuristic dist=31.8]: heuristic[score=56.8 >=25? → cloud] uTok=63(+0.8) kw=4(+56) |

### complex-refactor

> I need to plan a zero-downtime migration of our user table from MySQL to Postgres. Walk me through the dual-write strategy, validation, cutover, and rollback. Also describe what to do about in-flight …

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 8.6s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 11.1s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | cloud | gpt-5.5 | 12.6s | [router] strategy=rules → CLOUD (gpt-5.5) / conf=0.65 / rules: kw[cloud]: plan,strategy |
| heuristic | cloud | gpt-5.5 | 10.7s | [router] strategy=heuristic → CLOUD (gpt-5.5) / conf=0.58 / heuristic[score=28.9 >=25? → cloud] uTok=69(+0.9) kw=2(+28) |
| llm-classifier | cloud | gpt-5.5 | 10.8s | [router] strategy=llm-classifier → CLOUD (gpt-5.5) / conf=0.80 / llm-classifier(qwen3:0.6b): "COMPLEX" (493ms) |
| embedding-knn | cloud | gpt-5.5 | 10.9s | [router] strategy=embedding-knn → CLOUD (gpt-5.5) / conf=1.00 / embedding-knn[k=5]: cloud=5/5 (w=3.43 vs 0.00) (90ms) — top: "Plan a zero-downtime migration of our user table from MySQL " |
| cascade | cloud | gpt-5.5 | 12.4s | [router] strategy=cascade → CLOUD (gpt-5.5) / conf=0.84 / cascade[agree dist=3.9, llm=cloud]: heuristic[score=28.9 >=25? → cloud] uTok=69(+0.9) kw=2(+28) / llm-classifier(qwen3:0.6b): "COMPLEX" (119ms) |

### complex-perf

> Diagnose this performance regression: p99 latency jumped from 50ms to 800ms after our last deploy. Walk me through, step by step, how to find the root cause, what telemetry to check, what tools to run…

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 8.2s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 12.1s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | cloud | gpt-5.5 | 12.1s | [router] strategy=rules → CLOUD (gpt-5.5) / conf=0.65 / rules: kw[cloud]: step by step |
| heuristic | local | qwen3-coder:30b | 8.0s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.70 / heuristic[score=14.9 >=25? → local] uTok=71(+0.9) kw=1(+14) |
| llm-classifier | local | qwen3-coder:30b | 8.1s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (124ms) |
| embedding-knn | cloud | gpt-5.5 | 11.6s | [router] strategy=embedding-knn → CLOUD (gpt-5.5) / conf=1.00 / embedding-knn[k=5]: cloud=5/5 (w=3.24 vs 0.00) (41ms) — top: "Diagnose this performance regression: p99 latency went from " |
| cascade | local | qwen3-coder:30b | 8.2s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.88 / cascade[agree dist=10.1, llm=local]: heuristic[score=14.9 >=25? → local] uTok=71(+0.9) kw=1(+14) / llm-classifier(qwen3:0.6b): "SIMPLE" (158ms) |

<details><summary>heuristic-routed response excerpt</summary>

```
I'll walk you through a systematic approach to diagnose this 15x latency regression. Here's my step-by-step methodology: ## Phase 1: Initial Assessment & Data Collection **1. Confirm the Regression** - Verify the timing: when exactly did it
```

</details>

### complex-architecture

> Architect a streaming ingestion pipeline that handles 100k events/sec with at-least-once semantics, replay capability, and pluggable sinks. Compare two approaches in depth: Kafka + workers vs Pulsar +…

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 8.1s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 17.1s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | cloud | gpt-5.5 | 16.3s | [router] strategy=rules → CLOUD (gpt-5.5) / conf=0.65 / rules: kw[cloud]: architect,compare,comprehensive |
| heuristic | cloud | gpt-5.5 | 11.9s | [router] strategy=heuristic → CLOUD (gpt-5.5) / conf=1.00 / heuristic[score=57.0 >=25? → cloud] uTok=78(+1.0) kw=4(+56) |
| llm-classifier | local | qwen3-coder:30b | 8.4s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (208ms) |
| embedding-knn | cloud | gpt-5.5 | 14.7s | [router] strategy=embedding-knn → CLOUD (gpt-5.5) / conf=1.00 / embedding-knn[k=5]: cloud=5/5 (w=3.43 vs 0.00) (39ms) — top: "Architect a streaming ingestion pipeline that handles 100k e" |
| cascade | cloud | gpt-5.5 | 12.2s | [router] strategy=cascade → CLOUD (gpt-5.5) / conf=1.00 / cascade[trust-heuristic dist=32.0]: heuristic[score=57.0 >=25? → cloud] uTok=78(+1.0) kw=4(+56) |

### long-context

> Here is a long file (just imagine 800 lines of TypeScript with deep import graph). Refactor it into three modules with clear boundaries. Include a migration sequence that keeps tests passing throughou…

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 8.7s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 8.8s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | cloud | gpt-5.5 | 11.0s | [router] strategy=rules → CLOUD (gpt-5.5) / conf=0.65 / rules: kw[cloud]: long |
| heuristic | local | qwen3-coder:30b | 7.8s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.59 / heuristic[score=20.4 >=25? → local] uTok=508(+6.3) kw=1(+14) |
| llm-classifier | local | qwen3-coder:30b | 8.0s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (159ms) |
| embedding-knn | local | qwen3-coder:30b | 7.9s | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=0.58 / embedding-knn[k=5]: cloud=2/5 (w=1.27 vs 1.73) (67ms) — top: "Review this 800-line file and suggest a refactor plan with c" |
| cascade | local | qwen3-coder:30b | 8.0s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.85 / cascade[agree dist=4.6, llm=local]: heuristic[score=20.4 >=25? → local] uTok=508(+6.3) kw=1(+14) / llm-classifier(qwen3:0.6b): "SIMPLE" (123ms) |

<details><summary>heuristic-routed response excerpt</summary>

```
I'll help you refactor a large TypeScript file into three modules with clear boundaries and provide a migration sequence that keeps tests passing. Since you mentioned it's 800 lines with deep import graphs, I'll create a realistic example t
```

</details>

### ambiguous-short

> fix it

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 968ms | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 2.5s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 1.0s | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=2, codeBlocks=0) |
| heuristic | local | qwen3-coder:30b | 926ms | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=1.00 / heuristic[score=0.0 >=25? → local] uTok=2(+0.0) |
| llm-classifier | local | qwen3-coder:30b | 1.1s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (127ms) |
| embedding-knn | cloud | gpt-5.5 | 2.6s | [router] strategy=embedding-knn → CLOUD (gpt-5.5) / conf=0.81 / embedding-knn[k=5]: cloud=4/5 (w=2.19 vs 0.52) (55ms) — top: "Explain why this React component re-renders on every keystro" |
| cascade | local | qwen3-coder:30b | 1.1s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=1.00 / cascade[trust-heuristic dist=25.0]: heuristic[score=0.0 >=25? → local] uTok=2(+0.0) |

<details><summary>heuristic-routed response excerpt</summary>

```
I'd be happy to help you fix something, but I don't see any specific issue or code in your message. Could you please provide more details about what you'd like me to fix? For example: - Are you referring to code that needs debugging? - Is t
```

</details>

### tools-heavy

> List the 5 largest files in src/, count how many imports each has, then summarise. (You'll need to use shell tools.)

| strategy | choice | backend | elapsed | banner / error |
| --- | --- | --- | --- | --- |
| always-local | local | qwen3-coder:30b | 6.0s | [router] strategy=always-local → LOCAL (qwen3-coder:30b) / conf=1.00 / control: always-local |
| always-cloud | cloud | gpt-5.5 | 10.6s | [router] strategy=always-cloud → CLOUD (gpt-5.5) / conf=1.00 / control: always-cloud |
| rules | local | qwen3-coder:30b | 7.4s | [router] strategy=rules → LOCAL (qwen3-coder:30b) / conf=0.60 / rules: default-local (tokens=29, codeBlocks=0) |
| heuristic | local | qwen3-coder:30b | 7.9s | [router] strategy=heuristic → LOCAL (qwen3-coder:30b) / conf=0.99 / heuristic[score=0.4 >=25? → local] uTok=29(+0.4) |
| llm-classifier | local | qwen3-coder:30b | 6.4s | [router] strategy=llm-classifier → LOCAL (qwen3-coder:30b) / conf=0.80 / llm-classifier(qwen3:0.6b): "SIMPLE" (390ms) |
| embedding-knn | local | qwen3-coder:30b | 8.0s | [router] strategy=embedding-knn → LOCAL (qwen3-coder:30b) / conf=0.61 / embedding-knn[k=5]: cloud=2/5 (w=1.15 vs 1.80) (144ms) — top: "Sort the imports alphabetically" |
| cascade | local | qwen3-coder:30b | 7.0s | [router] strategy=cascade → LOCAL (qwen3-coder:30b) / conf=0.99 / cascade[trust-heuristic dist=24.6]: heuristic[score=0.4 >=25? → local] uTok=29(+0.4) |

<details><summary>heuristic-routed response excerpt</summary>

```
I'll help you find the 5 largest files in the src/ directory, count their imports, and provide a summary. Here's the solution using shell tools: ```bash # Find the 5 largest files in src/ and count imports find src/ -type f -name "*.js" -o 
```

</details>
