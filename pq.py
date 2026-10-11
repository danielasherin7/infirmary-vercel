"""Binary max-heap priority queue (written from scratch for the DSA project).

Priority rule: higher severity first; if severities are equal, the request that
arrived earlier (smaller seq) goes first.
push O(log n) | extract_max O(log n) | peek O(1) | sorted_list O(n log n)
"""


class PriorityQueue:
    def __init__(self):
        self.a = []

    def _before(self, x, y):
        if x["sev"] != y["sev"]:
            return x["sev"] > y["sev"]
        return x["seq"] < y["seq"]

    def push(self, item):
        self.a.append(item)
        i = len(self.a) - 1
        while i > 0:                                  # sift up
            p = (i - 1) // 2
            if not self._before(self.a[i], self.a[p]):
                break
            self.a[i], self.a[p] = self.a[p], self.a[i]
            i = p

    def peek(self):
        return self.a[0] if self.a else None

    def extract_max(self):
        if not self.a:
            return None
        top, last = self.a[0], self.a.pop()
        if self.a:
            self.a[0] = last
            i, n = 0, len(self.a)
            while True:                               # sift down
                l, r, m = 2 * i + 1, 2 * i + 2, i
                if l < n and self._before(self.a[l], self.a[m]):
                    m = l
                if r < n and self._before(self.a[r], self.a[m]):
                    m = r
                if m == i:
                    break
                self.a[i], self.a[m] = self.a[m], self.a[i]
                i = m
        return top

    def __len__(self):
        return len(self.a)

    def sorted_list(self):
        c = PriorityQueue()
        c.a = list(self.a)
        out = []
        while len(c):
            out.append(c.extract_max())
        return out
