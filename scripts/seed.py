"""Seed the database with 5 famous CS papers and cross-references for demo purposes.

Usage:
    python scripts/seed.py

Requires DATABASE_URL env var or defaults to local docker-compose DB.
"""

import asyncio
import json
import os
import uuid

import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://researchgraph:researchgraph_secret@localhost:5432/researchgraph_db",
)

# ── Famous CS papers ────────────────────────────────────────────────
PAPERS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "1706.03762")),
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "authors": json.dumps(["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"]),
        "categories": json.dumps(["cs.CL", "cs.LG"]),
        "published_date": "2017-06-12T00:00:00Z",
        "pdf_url": "https://arxiv.org/pdf/1706.03762",
        "references": json.dumps(["1512.03385", "1409.0473", "1706.03762"]),
        "cited_by": json.dumps(["1810.04805", "2005.14165"]),
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "1512.03385")),
        "arxiv_id": "1512.03385",
        "title": "Deep Residual Learning for Image Recognition",
        "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
        "authors": json.dumps(["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"]),
        "categories": json.dumps(["cs.CV", "cs.LG"]),
        "published_date": "2015-12-10T00:00:00Z",
        "pdf_url": "https://arxiv.org/pdf/1512.03385",
        "references": json.dumps([]),
        "cited_by": json.dumps(["1706.03762"]),
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "1810.04805")),
        "arxiv_id": "1810.04805",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
        "authors": json.dumps(["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"]),
        "categories": json.dumps(["cs.CL"]),
        "published_date": "2018-10-11T00:00:00Z",
        "pdf_url": "https://arxiv.org/pdf/1810.04805",
        "references": json.dumps(["1706.03762"]),
        "cited_by": json.dumps(["2005.14165"]),
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "2005.14165")),
        "arxiv_id": "2005.14165",
        "title": "Language Models are Few-Shot Learners",
        "abstract": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. We show that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches.",
        "authors": json.dumps(["Tom B. Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah"]),
        "categories": json.dumps(["cs.CL", "cs.LG"]),
        "published_date": "2020-05-28T00:00:00Z",
        "pdf_url": "https://arxiv.org/pdf/2005.14165",
        "references": json.dumps(["1706.03762", "1810.04805"]),
        "cited_by": json.dumps([]),
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "1409.0473")),
        "arxiv_id": "1409.0473",
        "title": "Neural Machine Translation by Jointly Learning to Align and Translate",
        "abstract": "Neural machine translation is a recently proposed approach to machine translation. Unlike the traditional statistical machine translation, the neural machine translation aims at building a single neural network that can be jointly tuned to maximize the translation performance. We conjecture that the use of a fixed-length vector is a bottleneck in improving the performance of this basic encoder-decoder architecture, and propose to extend this by allowing a model to automatically search for parts of a source sentence that are relevant to predicting a target word.",
        "authors": json.dumps(["Dzmitry Bahdanau", "Kyunghyun Cho", "Yoshua Bengio"]),
        "categories": json.dumps(["cs.CL", "stat.ML"]),
        "published_date": "2014-09-01T00:00:00Z",
        "pdf_url": "https://arxiv.org/pdf/1409.0473",
        "references": json.dumps([]),
        "cited_by": json.dumps(["1706.03762"]),
    },
]


async def seed():
    conn = await asyncpg.connect(DATABASE_URL)

    print("Seeding database with 5 CS papers...\n")

    inserted = 0
    skipped = 0

    for paper in PAPERS:
        # Check if paper already exists
        existing = await conn.fetchrow(
            "SELECT arxiv_id FROM papers WHERE arxiv_id = $1",
            paper["arxiv_id"],
        )

        if existing:
            print(f"  ~ SKIP  {paper['title']} (already exists)")
            skipped += 1
            continue

        await conn.execute(
            """
            INSERT INTO papers (id, arxiv_id, title, abstract, authors, categories,
                                published_date, pdf_url, references, cited_by, is_processed)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::timestamptz, $8, $9::jsonb, $10::jsonb, false)
            """,
            uuid.UUID(paper["id"]),
            paper["arxiv_id"],
            paper["title"],
            paper["abstract"],
            paper["authors"],
            paper["categories"],
            paper["published_date"],
            paper["pdf_url"],
            paper["references"],
            paper["cited_by"],
        )
        print(f"  + ADD   {paper['title']}")
        inserted += 1

    await conn.close()
    print(f"\nDone! Inserted {inserted}, skipped {skipped}.")
    print("Graph is ready at http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(seed())
