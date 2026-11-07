# Qwen 백본 라이선스와 원본 보존

확인일: 2026-11-06. 백본은 `Qwen/Qwen3-4B-Instruct-2507`, 고정 revision은 `cdbee75f17c01a7cc42f958dc650907174af0554`입니다. 이 revision의 [Qwen 공식 LICENSE](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE)는 Apache License 2.0입니다.

[Apache 2.0 공식 원문](https://www.apache.org/licenses/LICENSE-2.0)의 제2조는 조건에 따른 복제·수정·파생물 작성·배포 등을 허용하며 상업적 이용을 제한하지 않습니다. 재배포에는 제4조의 다음 조건이 적용됩니다.

- 수령인에게 라이선스 사본을 제공합니다(4(a)).
- 수정한 파일에는 수정 사실을 명확히 표시합니다(4(b)).
- 배포하는 파생물의 소스 형태에서는 관련 저작권·특허·상표·출처 고지를 유지합니다(4(c)).
- 원본 배포물에 `NOTICE`가 있으면 해당되는 출처 고지를 읽을 수 있는 형태로 함께 전달합니다. 이 고지는 라이선스 자체를 변경하지 않습니다(4(d)).

제6조는 통상적인 출처 설명 등의 범위를 제외한 상표 사용권을 부여하지 않습니다. 제7조는 권원·비침해·상품성·특정 목적 적합성을 포함한 보증을 제공하지 않습니다. 따라서 Apache 허용 범위를 모든 이용 상황에 대한 권리 보증으로 해석하지 않습니다.

이번 산출물은 원본 백본을 고정하고 영·일 WordNet 어휘 과제로 학습한 **별도 LoRA 어댑터**입니다. 원본에 병합하지 않았으며 전체 백본 가중치를 어댑터 패키지에 넣지 않습니다. 학습 전 기록 (`runs/wordnet-lora-2026-11-06/base-before.json`)과 학습 후 기록 (`runs/wordnet-lora-2026-11-06/base-after.json`)의 원본 12개 파일 크기·SHA256 목록은 모두 일치합니다. 이는 원본 파일이 보존됐다는 확인이며, 이용 허가는 위 라이선스 조건에서 별도로 확인합니다.

어댑터 모델 카드 (`artifacts/qwen3-4b-wordnet-en-ja-lora-v1/README.md`)에 백본·revision·실제 학습 사실·별도 LoRA임을 표시하고, 원본 LICENSE 사본 (`artifacts/qwen3-4b-wordnet-en-ja-lora-v1/LICENSE`)을 동봉합니다. 캐시의 원본 LICENSE와 동봉본은 다음 SHA256으로 일치합니다.

`832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`

WordNet 데이터의 조건은 백본 Apache 라이선스와 별개입니다. 어댑터 NOTICE (`artifacts/qwen3-4b-wordnet-en-ja-lora-v1/NOTICE`)에 Japanese WordNet·Princeton WordNet·Open English WordNet·OEWN 계승 WordNet의 네 원문 라이선스와 출처·변환 고지를 보존합니다. 어댑터의 `apache-2.0` 표기가 데이터 조건을 대체하거나 fiXmArge·게임 자료의 학습 허가를 뜻하지 않습니다.
