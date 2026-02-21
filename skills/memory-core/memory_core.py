#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Core - 项目级 RAG 记忆管理系统
存储在项目内，支持向量语义检索，原子写入确保一致性

注意：FAISS 在 Windows 上无法写入包含中文字符的路径，
因此向量索引存储在全局目录（E:\trae-memory\），
记忆数据存储在项目内。
"""

import argparse
import json
import os
import sys
import threading
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError as e:
    print(f"错误: 缺少依赖 - {e}", file=sys.stderr)
    print("请运行: pip install sentence-transformers faiss-cpu numpy", file=sys.stderr)
    sys.exit(1)


def _has_chinese(path: str) -> bool:
    for char in path:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def _get_safe_vector_path(project_root: Path) -> Path:
    project_root_str = str(project_root)
    if not _has_chinese(project_root_str):
        return project_root / '.trae' / 'memory' / 'core' / 'vectors.index'
    
    global_dir = Path(os.environ.get('TRAE_MEMORY_DIR', r'E:\trae-memory'))
    global_dir.mkdir(parents=True, exist_ok=True)
    
    project_hash = hashlib.md5(project_root_str.encode()).hexdigest()[:8]
    return global_dir / f'vectors_{project_hash}.index'


class MemoryCore:
    """项目级记忆管理器"""
    
    MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
    _model = None
    _model_lock = threading.Lock()
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = self._find_project_root()
        
        self.project_root = Path(project_root)
        self.memory_dir = self.project_root / '.trae' / 'memory' / 'core'
        self.memory_file = self.memory_dir / 'memory.json'
        self.readable_file = self.memory_dir / 'memory.md'
        self.vector_file = _get_safe_vector_path(self.project_root)
        
        self._ensure_dirs()
        self._load_model()
        self._load_data()
    
    def _find_project_root(self) -> str:
        current = Path.cwd()
        while current != current.parent:
            if (current / '.trae').exists():
                return str(current)
            current = current.parent
        return str(Path.cwd())
    
    def _ensure_dirs(self):
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.vector_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_model(self):
        with MemoryCore._model_lock:
            if MemoryCore._model is None:
                model_cache = self.project_root / '.trae' / 'models'
                model_cache.mkdir(parents=True, exist_ok=True)
                
                local_model = self._find_local_model(model_cache)
                if local_model:
                    print("提示: 加载向量模型（本地）...", file=sys.stderr)
                    MemoryCore._model = SentenceTransformer(str(local_model))
                else:
                    print(f"提示: 首次使用，下载向量模型...", file=sys.stderr)
                    MemoryCore._model = SentenceTransformer(
                        self.MODEL_NAME,
                        cache_folder=str(model_cache)
                    )
                print(f"提示: 模型加载完成（维度: {MemoryCore._model.get_sentence_embedding_dimension()}）", file=sys.stderr)
            
            self.model = MemoryCore._model
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def _find_local_model(self, cache_dir: Path) -> Optional[Path]:
        if not cache_dir.exists():
            return None
        
        hf_pattern = f'*sentence-transformers*{self.MODEL_NAME}*'
        for model_dir in cache_dir.glob(hf_pattern):
            snapshots = model_dir / 'snapshots'
            if snapshots.exists():
                for snap in snapshots.iterdir():
                    if (snap / 'config.json').exists():
                        return snap
        return None
    
    def _load_data(self):
        self.memories: List[Dict] = []
        self.index: Optional[faiss.Index] = None
        
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = data.get('memories', [])
            except Exception as e:
                print(f"警告: 加载记忆文件失败 - {e}", file=sys.stderr)
        
        if self.vector_file.exists():
            try:
                self.index = faiss.read_index(str(self.vector_file))
            except Exception as e:
                print(f"警告: 加载向量索引失败 - {e}", file=sys.stderr)
                self.index = None
        
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        self._sync_check()
    
    def _sync_check(self):
        index_count = self.index.ntotal
        memory_count = len(self.memories)
        
        if index_count != memory_count:
            print(f"警告: 索引({index_count})与记忆({memory_count})不同步，建议运行 rebuild", file=sys.stderr)
    
    def _save_all(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': '1.0.0',
                    'updated': datetime.now().isoformat(),
                    'total': len(self.memories),
                    'vector_path': str(self.vector_file),
                    'memories': self.memories
                }, f, ensure_ascii=False, indent=2)
            
            faiss.write_index(self.index, str(self.vector_file))
            
            self._update_readable_file()
            
            return True
        except Exception as e:
            print(f"错误: 保存失败 - {e}", file=sys.stderr)
            return False
    
    def _update_readable_file(self):
        lines = ["# Memory Database\n\n"]
        lines.append(f"> 向量索引: `{self.vector_file}`\n\n")
        
        errors = [m for m in self.memories if m['type'] == 'error']
        successes = [m for m in self.memories if m['type'] == 'success']
        decisions = [m for m in self.memories if m['type'] == 'decision']
        contexts = [m for m in self.memories if m['type'] == 'context']
        
        lines.append("## Error Patterns\n\n")
        for m in errors:
            lines.append(f"### {m['id']}: {m.get('error_type', 'N/A')}\n")
            lines.append(f"- Wrong: {m.get('wrong', 'N/A')}\n")
            lines.append(f"- Right: {m.get('right', 'N/A')}\n")
            lines.append(f"- Date: {m['created']}\n\n")
        
        lines.append("## Success Patterns\n\n")
        for m in successes:
            lines.append(f"### {m['id']}: {m.get('intent', 'N/A')}\n")
            lines.append(f"- Steps: {json.dumps(m.get('steps', []), ensure_ascii=False)}\n")
            lines.append(f"- Date: {m['created']}\n\n")
        
        lines.append("## Decisions\n\n")
        for m in decisions:
            lines.append(f"### {m['id']}: {m.get('choice', 'N/A')}\n")
            lines.append(f"- Reason: {m.get('reason', 'N/A')}\n")
            lines.append(f"- Date: {m['created']}\n\n")
        
        lines.append("## Context\n\n")
        for m in contexts:
            lines.append(f"### {m['id']}\n")
            lines.append(f"- Content: {m.get('content', 'N/A')[:100]}...\n")
            lines.append(f"- Date: {m['created']}\n\n")
        
        with open(self.readable_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def _get_next_id(self, prefix: str) -> str:
        max_id = 0
        for m in self.memories:
            if m['id'].startswith(f'{prefix}-'):
                try:
                    num = int(m['id'].split('-')[1])
                    max_id = max(max_id, num)
                except (ValueError, IndexError):
                    pass
        return f"{prefix}-{max_id + 1:05d}"
    
    def _is_duplicate(self, content: str, threshold: float = 0.95) -> bool:
        if not self.memories:
            return False
        
        try:
            embedding = self.model.encode([content], convert_to_numpy=True)
            distances, indices = self.index.search(embedding, 1)
            
            if indices[0][0] >= 0:
                similarity = 1 / (1 + distances[0][0])
                return similarity >= threshold
        except Exception:
            pass
        return False
    
    def _add_to_index(self, content: str, memory_id: str, memory_type: str, **extra):
        if self._is_duplicate(content):
            print(f"警告: 检测到重复内容，跳过", file=sys.stderr)
            return False
        
        embedding = self.model.encode([content], convert_to_numpy=True)
        self.index.add(embedding)
        
        memory = {
            'id': memory_id,
            'type': memory_type,
            'content': content,
            'created': datetime.now().isoformat(),
            **extra
        }
        self.memories.append(memory)
        
        if self._save_all():
            print(f"已记录: [{memory_id}] {memory_type}", file=sys.stderr)
            return True
        return False
    
    def add_error(self, error_type: str, wrong: str, right: str, tags: List[str] = None):
        content = f"{error_type}: {wrong} -> {right}"
        memory_id = self._get_next_id('ERR')
        return self._add_to_index(
            content, memory_id, 'error',
            error_type=error_type, wrong=wrong, right=right,
            tags=tags or []
        )
    
    def add_success(self, intent: str, steps: List[str], tags: List[str] = None):
        content = f"{intent}: {' '.join(steps)}"
        memory_id = self._get_next_id('FEAT')
        return self._add_to_index(
            content, memory_id, 'success',
            intent=intent, steps=steps,
            tags=tags or []
        )
    
    def add_decision(self, choice: str, reason: str, tags: List[str] = None):
        content = f"{choice}: {reason}"
        memory_id = self._get_next_id('DEC')
        return self._add_to_index(
            content, memory_id, 'decision',
            choice=choice, reason=reason,
            tags=tags or []
        )
    
    def add_context(self, content: str, tags: List[str] = None):
        memory_id = self._get_next_id('CTX')
        return self._add_to_index(
            content, memory_id, 'context',
            tags=tags or []
        )
    
    def retrieve(self, query: str, top_k: int = 5, min_similarity: float = 0.05) -> List[Dict]:
        if not self.memories:
            return []
        
        embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(embedding, min(top_k, len(self.memories)))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.memories):
                similarity = 1 / (1 + distances[0][i])
                if similarity >= min_similarity:
                    mem = self.memories[idx].copy()
                    mem['similarity'] = round(similarity, 3)
                    results.append(mem)
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def list_all(self) -> List[Dict]:
        return self.memories.copy()
    
    def rebuild_index(self):
        print(f"重建索引: {len(self.memories)} 条记忆...", file=sys.stderr)
        
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        if self.memories:
            contents = [m['content'] for m in self.memories]
            embeddings = self.model.encode(contents, convert_to_numpy=True)
            self.index.add(embeddings)
        
        faiss.write_index(self.index, str(self.vector_file))
        print(f"重建完成: 索引 {self.index.ntotal} 条", file=sys.stderr)
        print(f"索引位置: {self.vector_file}", file=sys.stderr)
        return True
    
    def stats(self) -> Dict:
        type_counts = {}
        for m in self.memories:
            t = m['type']
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            'total': len(self.memories),
            'index_size': self.index.ntotal,
            'sync': self.index.ntotal == len(self.memories),
            'by_type': type_counts,
            'memory_file': str(self.memory_file),
            'vector_file': str(self.vector_file)
        }
    
    def get_daily_log_path(self, date: str = None) -> Path:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return self.memory_dir / 'daily' / f'{date}.md'
    
    def write_daily_log(self, content: str, date: str = None):
        log_path = self.get_daily_log_path(date)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = f"\n## [{timestamp}]\n{content}\n"
        
        if not log_path.exists():
            header = f"# 每日日志 - {date or datetime.now().strftime('%Y-%m-%d')}\n"
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(header)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        print(f"已写入每日日志: {log_path}", file=sys.stderr)
        return True
    
    def load_daily_logs(self, days: int = 2) -> str:
        logs = []
        today = datetime.now()
        
        for i in range(days):
            date = (today - __import__('datetime').timedelta(days=i)).strftime('%Y-%m-%d')
            log_path = self.get_daily_log_path(date)
            
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logs.append(f"=== {date} ===\n{content}")
        
        return '\n\n'.join(logs) if logs else "无每日日志"


def main():
    parser = argparse.ArgumentParser(description='Memory Core - 项目级记忆管理')
    parser.add_argument('--action', required=True,
                       choices=['retrieve', 'success', 'error', 'decision', 'context', 'list', 'rebuild', 'stats', 'daily-log', 'load-daily'])
    
    parser.add_argument('--query', help='检索查询')
    parser.add_argument('--top_k', type=int, default=5)
    parser.add_argument('--min_similarity', type=float, default=0.05)
    
    parser.add_argument('--intent', help='成功模式意图')
    parser.add_argument('--steps', help='步骤（逗号分隔）')
    
    parser.add_argument('--type', help='错误类型')
    parser.add_argument('--wrong', help='错误做法')
    parser.add_argument('--right', help='正确做法')
    
    parser.add_argument('--choice', help='决策选择')
    parser.add_argument('--reason', help='决策理由')
    
    parser.add_argument('--content', help='上下文内容')
    parser.add_argument('--tags', help='标签（逗号分隔）')
    
    args = parser.parse_args()
    
    manager = MemoryCore()
    
    if args.action == 'retrieve':
        if not args.query:
            print("错误: 需要 --query 参数", file=sys.stderr)
            sys.exit(1)
        
        results = manager.retrieve(args.query, args.top_k, args.min_similarity)
        
        print(f"\n检索: {args.query}")
        print(f"阈值: {args.min_similarity}")
        print("=" * 50)
        
        if results:
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['id']}] 相似度={r['similarity']}")
                print(f"   类型: {r['type']}")
                print(f"   内容: {r['content'][:80]}...")
        else:
            print("\n未找到相关记忆")
    
    elif args.action == 'success':
        if not args.intent or not args.steps:
            print("错误: 需要 --intent 和 --steps 参数", file=sys.stderr)
            sys.exit(1)
        steps = [s.strip() for s in args.steps.split(',')]
        tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
        manager.add_success(args.intent, steps, tags)
    
    elif args.action == 'error':
        if not args.type or not args.wrong or not args.right:
            print("错误: 需要 --type, --wrong, --right 参数", file=sys.stderr)
            sys.exit(1)
        tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
        manager.add_error(args.type, args.wrong, args.right, tags)
    
    elif args.action == 'decision':
        if not args.choice or not args.reason:
            print("错误: 需要 --choice 和 --reason 参数", file=sys.stderr)
            sys.exit(1)
        tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
        manager.add_decision(args.choice, args.reason, tags)
    
    elif args.action == 'context':
        if not args.content:
            print("错误: 需要 --content 参数", file=sys.stderr)
            sys.exit(1)
        tags = [t.strip() for t in args.tags.split(',')] if args.tags else []
        manager.add_context(args.content, tags)
    
    elif args.action == 'list':
        memories = manager.list_all()
        print(f"\n共 {len(memories)} 条记忆:")
        for m in memories:
            print(f"  [{m['id']}] {m['type']}: {m['content'][:50]}...")
    
    elif args.action == 'rebuild':
        manager.rebuild_index()
    
    elif args.action == 'stats':
        stats = manager.stats()
        print(f"\n记忆统计:")
        print(f"  总数: {stats['total']}")
        print(f"  索引: {stats['index_size']}")
        print(f"  同步: {'是' if stats['sync'] else '否'}")
        print(f"  分类: {stats['by_type']}")
        print(f"  记忆文件: {stats['memory_file']}")
        print(f"  向量索引: {stats['vector_file']}")
    
    elif args.action == 'daily-log':
        if not args.content:
            print("错误: 需要 --content 参数", file=sys.stderr)
            sys.exit(1)
        manager.write_daily_log(args.content)
    
    elif args.action == 'load-daily':
        days = args.top_k if args.top_k else 2
        logs = manager.load_daily_logs(days)
        print(f"\n最近 {days} 天的日志:")
        print("=" * 50)
        print(logs)


if __name__ == '__main__':
    main()
