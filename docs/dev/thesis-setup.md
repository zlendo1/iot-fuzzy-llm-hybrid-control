Faculty of Electrical Engineering, University of Sarajevo

Department of Computer Science and Informatics

**Full Professor Dr. Samim Konjicija, Dipl. Eng. El.**

Sarajevo, January 6, 2026

______________________________________________________________________

# **Fuzzy-LLM Hybrid Approach for Rule-Based Management of IoT Systems**

## Assignment Description

Within the scope of this thesis, it is necessary to research and implement a
hybrid approach that combines **fuzzy logic** and **large language models
(LLMs)** for managing IoT systems using rules expressed in natural language. The
core idea is to use fuzzy logic as a **semantic bridge** between raw numerical
sensor values and linguistic concepts that an LLM can understand and process.

The candidate is expected to realize a system in which **membership functions
and linguistic variables are defined in JSON format**, enabling dynamic
configuration without the need for model retraining. The LLM used in the system
must support **offline execution**, which is of critical importance for IoT
environments with limited internet connectivity or strict privacy requirements.

The system should allow users to define control rules in **free-form natural
language**, where the fuzzy module translates sensor values into qualitative
descriptions (e.g., *“temperature is high”*, *“humidity is moderate”*) that the
LLM uses for decision-making.

Within this work, the candidate should:

- Conduct an analysis of existing approaches to integrating fuzzy logic and LLM
  technologies, and identify the advantages and disadvantages of different
  architectures for IoT management.
- Design and implement a fuzzy module that transforms numerical sensor data into
  linguistic descriptions, using JSON format for specifying membership functions
  and linguistic variables.
- Select and configure a suitable **offline LLM** (e.g., LLaMA, Mistral, or a
  similar model with up to 7B parameters) capable of efficient operation on
  resource-constrained edge devices.
- Develop a mechanism for interpreting natural language rules and mapping them
  to concrete IoT device control actions.
- Implement a prototype system that demonstrates the functionality of the
  proposed approach in a concrete IoT scenario (e.g., smart home, industrial
  monitoring, or agricultural automation).
- Conduct a system evaluation through experiments that measure rule
  interpretation accuracy, response time, and overall usability for end users.

______________________________________________________________________

## Significance of the Work

The significance of this thesis lies in its **innovative approach**, which
combines the interpretability of fuzzy logic with the flexibility of large
language models. Fuzzy logic enables transparent and understandable mapping of
sensor values to qualitative categories, while LLMs provide the ability to
define complex control rules in natural language without the need for
programming.

Offline execution ensures **data privacy**, **low latency**, and functionality
in environments without a stable internet connection. Successful implementation
of this system will enable more accessible automation of IoT environments for
users without technical backgrounds and open new possibilities for intuitive
management of complex systems.

______________________________________________________________________

## Initial Literature

- Morales Aguilera, F. (2024). *“Synergistic Intelligence: Enhancing Large
  Language Models with Fuzzy Inference Systems.”* Medium – The Deep Hub.
- Kalita, A. (2025). *“Talk with the Things: Integrating LLMs into IoT
  Networks.”* arXiv preprint arXiv:2507.17865.
- Wang, J., et al. (2024). *“Integrating Large Language Models with Internet of
  Things Applications.”* arXiv preprint arXiv:2410.19223.
- Liu, X., et al. (2024). *“LLMind: Orchestrating AI and IoT with LLMs for
  Complex Task Execution.”* arXiv preprint arXiv:2312.09007.
- Zhang, Y., et al. (2025). *“LACE: Say What You Mean – Natural Language Access
  Control with Large Language Models for Internet of Things.”* arXiv preprint
  arXiv:2505.23835.
