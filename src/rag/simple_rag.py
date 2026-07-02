"""
RAG Leve por Tags + BM25 Simplificado.
Zero dependências de ML — usa apenas correspondência de palavras-chave.
"""

import json
import re
from collections import Counter
from math import log
from typing import List, Dict, Optional
from pathlib import Path


class SimpleRAG:
    def __init__(self, corpus_path: str):
        """
        Inicializa o RAG com um arquivo corpus.jsonl.

        Cada linha deve ser um JSON com:
        {
            "id": int,
            "assunto": str,
            "tags": list[str],
            "enunciado": str,
            "resolucao": str
        }
        """
        self.docs: List[Dict] = []
        self.tag_index: Dict[str, List[Dict]] = {}

        path = Path(corpus_path)
        if not path.exists():
            raise FileNotFoundError(f"Corpus não encontrado: {corpus_path}")

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    doc = json.loads(line)
                    self.docs.append(doc)
                    for tag in doc.get("tags", []):
                        tag_lower = tag.lower().strip()
                        if tag_lower:
                            self.tag_index.setdefault(tag_lower, []).append(doc)

        self._precompute_idf()

    def _precompute_idf(self):
        """Pré-computa o IDF para o BM25 simplificado."""
        doc_count = len(self.docs)
        if doc_count == 0:
            self.idf = {}
            return

        word_doc_count = Counter()
        for doc in self.docs:
            words = set(re.findall(r'\w+', doc.get("enunciado", "").lower()))
            for word in words:
                word_doc_count[word] += 1

        self.idf = {
            word: log((doc_count + 1) / (1 + count))
            for word, count in word_doc_count.items()
        }

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Busca os documentos mais relevantes para a consulta.

        Estratégia:
        1. Tenta match por tags (prioritário)
        2. Fallback para BM25 simplificado
        """
        query_lower = query.lower()

        # 1. Busca por tags
        query_tags = self._extract_tags(query_lower)
        if query_tags:
            candidates = []
            for tag in query_tags:
                candidates.extend(self.tag_index.get(tag, []))

            if candidates:
                doc_scores = Counter(d.get("id", id(d)) for d in candidates)
                top_ids = [doc_id for doc_id, _ in doc_scores.most_common(top_k)]

                result = []
                for doc_id in top_ids:
                    for doc in self.docs:
                        if doc.get("id") == doc_id:
                            result.append(doc)
                            break
                return result

        # 2. Fallback: BM25 simplificado
        return self._bm25_search(query_lower, top_k)

    def _extract_tags(self, text: str) -> List[str]:
        """
        Extrai tags por palavra-chave — expandido para Matemática, Física, Química, Biologia.
        """
        tag_map = {
            # -- Matemática --
            "equacao": ["equacao_1grau", "equacao_2grau"],
            "funcao": ["funcao_afim", "funcao_quadratica"],
            "parabola": ["funcao_quadratica"],
            "bhaskara": ["equacao_2grau", "funcao_quadratica"],
            "vertice": ["funcao_quadratica"],
            "raiz": ["equacao_2grau"],
            "afim": ["funcao_afim"],
            "linear": ["funcao_afim"],

            # -- Física --
            "velocidade": ["muv", "cinematica"],
            "aceleracao": ["muv", "cinematica"],
            "movimento": ["muv", "cinematica"],
            "torricelli": ["muv"],
            "forca": ["leis_de_newton"],
            "massa": ["leis_de_newton", "estequiometria"],
            "energia": ["trabalho_energia"],

            # -- Química --
            "reacao": ["estequiometria", "quimica_geral"],
            "mol": ["estequiometria"],
            "massa molar": ["estequiometria"],
            "atomo": ["modelos_atomicos"],
            "ligacao": ["ligacoes_quimicas"],
            "ph": ["solucoes"],
            "ácido": ["solucoes"],

            # -- Biologia --
            "mendel": ["genetica"],
            "gene": ["genetica"],
            "alelo": ["genetica"],
            "cruzamento": ["genetica"],
            "celula": ["citologia"],
            "dna": ["genetica", "biologia_molecular"],
            "evolucao": ["evolucao"],
            "ecossistema": ["ecologia"],
        }

        found = []
        seen = set()
        for word, tags in tag_map.items():
            if word in text:
                for t in tags:
                    if t not in seen:
                        seen.add(t)
                        found.append(t)
        return found

    def _bm25_search(self, query: str, top_k: int) -> List[Dict]:
        """BM25 simplificado — fallback quando tags não encontram nada."""
        words = re.findall(r'\w+', query.lower())
        if not words or not self.docs:
            return []

        scores = []
        for doc in self.docs:
            doc_words = re.findall(r'\w+', doc.get("enunciado", "").lower())
            score = 0.0
            for word in words:
                idf_val = self.idf.get(word, 0)
                tf = doc_words.count(word)
                score += idf_val * (tf * 1.5) / (tf + 1.5)
            scores.append((doc, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scores[:top_k]]

    def get_stats(self) -> Dict:
        """Retorna estatísticas do RAG para diagnóstico."""
        return {
            "total_docs": len(self.docs),
            "unique_tags": len(self.tag_index),
            "tags": list(self.tag_index.keys())[:10],
        }
