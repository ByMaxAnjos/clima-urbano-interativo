# modules/avaliacao.py

import streamlit as st
import pandas as pd
from datetime import datetime

def renderizar_pagina():
    """Renderiza o formulário de avaliação da plataforma."""

    st.markdown("""
    <div class="module-header">
        <h1>📝 Formulário de Avaliação</h1>
        <p>Coletamos críticas, sugestões e ideias de estudantes e professores para aprimorar a Plataforma Clima Urbano Interativo.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.header("1️⃣ Perfil do Respondente")

    papel = st.radio(
        "1. Qual seu papel principal?",
        ["Estudante do ensino básico", "Estudante do ensino superior", "Professor/Educador", "Outro"]
    )

    nivel_ensino = st.radio(
        "2. Em qual nível de ensino você atua ou estuda?",
        ["Ensino fundamental anos iniciais", "Ensino fundamental anos finais", "Ensino médio", "Ensino superior", "Pós-graduação"]
    )

    contato_climatologia = st.radio(
        "3. Você já teve contato com estudos ou projetos de climatologia ou mudanças climáticas antes?",
        ["Sim", "Não"]
    )

    st.markdown("---")
    st.header("2️⃣ Experiência e Expectativas")

    clareza_recursos = st.radio(
        "4. Como você avalia os recursos atuais da plataforma em termos de clareza e compreensão?",
        ["Muito claro", "Parcialmente claro", "Pouco claro", "Confuso"]
    )

    funcionalidades = st.multiselect(
        "5. Quais funcionalidades você considera essenciais na plataforma?",
        ["Simulações interativas", "Gráficos/mapas dinâmicos", "Vídeos/Animações",
         "Glossário de termos científicos", "Jogos ou quizzes", "Estudos de caso locais",
         "Ferramentas de comparação de cenários", "Outras"]
    )

    conceitos_prioridade = st.text_area(
        "6. Quais palavras ou conceitos você acha que deveriam estar explicados com prioridade?"
    )

    apresentacao_conceitos = st.radio(
        "7. Como você prefere que os conceitos mais complexos sejam apresentados?",
        ["Texto simples", "Infográficos", "Vídeos", "Animações interativas", "Exemplos práticos"]
    )

    st.markdown("---")
    st.header("3️⃣ Usabilidade e Design")

    navegabilidade = st.radio(
        "8. Você acha a plataforma fácil de navegar?",
        ["Muito fácil", "Mais ou menos", "Difícil"]
    )

    avaliacao_visual = st.radio(
        "9. Como você avalia o visual/design da plataforma?",
        ["Muito atraente", "Adequado", "Precisa melhorar", "Desagradável/confuso"]
    )

    dispositivos = st.radio(
        "10. A plataforma funciona bem em diferentes dispositivos?",
        ["Sempre funciona bem", "Na maioria das vezes", "Às vezes com dificuldades", "Quase nunca funciona bem"]
    )

    st.markdown("---")
    st.header("4️⃣ Conteúdo Pedagógico")

    alinhamento = st.radio(
        "11. Os temas abordados estão alinhados com o que você gostaria de aprender ou ensinar?",
        ["Muito alinhados", "Parcialmente alinhados", "Pouco alinhados", "Não alinhados"]
    )

    participacao_ativa = st.radio(
        "12. A plataforma estimula sua participação ativa no aprendizado?",
        ["Sim, bastante", "Parcialmente", "Pouco", "Nada"]
    )

    aprendizado_pratico = st.text_area(
        "13. Como o aprendizado poderia se tornar mais prático ou conectado com a realidade local?"
    )

    st.markdown("---")
    st.header("5️⃣ Comunicação e Linguagem")

    linguagem_adequada = st.radio(
        "14. A linguagem usada na plataforma é adequada para seu nível de conhecimento?",
        ["Muito acessível", "Um pouco técnica, mas compreensível", "Técnica demais/difícil"]
    )

    termos_confusos = st.text_area(
        "15. Há termos, jargões ou expressões que você não entendeu ou achou confusos?"
    )

    suporte_estilos = st.radio(
        "16. A plataforma oferece suporte para diferentes estilos de aprendizagem?",
        ["Sim, atende bem", "Em parte", "Não, falta diversidade"]
    )

    st.markdown("---")
    st.header("6️⃣ Avaliação Geral e Sugestões")

    gostos_plataforma = st.text_area(
        "17. O que você mais gosta na proposta da Plataforma Clima Urbano Interativo?"
    )

    desafios = st.text_area(
        "18. O que você considera o maior desafio ou limitação até agora na plataforma?"
    )

    sugestao_funcionalidade = st.text_area(
        "19. Se pudesse adicionar uma funcionalidade, recurso ou estratégia, o que seria?"
    )

    recomendacao = st.text_area(
        "20. Avalie de 0 a 10: quanto você recomendaria essa plataforma para colegas ou alunos?"
    )

    outras_sugestoes = st.text_area(
        "21. Outras sugestões, críticas ou comentários que você deseja compartilhar?"
    )

    st.markdown("---")
    st.header("Enviar Avaliação")

    if st.button("📤 Enviar"):
        resposta = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "papel": papel,
            "nivel_ensino": nivel_ensino,
            "contato_climatologia": contato_climatologia,
            "clareza_recursos": clareza_recursos,
            "funcionalidades": ", ".join(funcionalidades),
            "conceitos_prioridade": conceitos_prioridade,
            "apresentacao_conceitos": apresentacao_conceitos,
            "navegabilidade": navegabilidade,
            "avaliacao_visual": avaliacao_visual,
            "dispositivos": dispositivos,
            "alinhamento": alinhamento,
            "participacao_ativa": participacao_ativa,
            "aprendizado_pratico": aprendizado_pratico,
            "linguagem_adequada": linguagem_adequada,
            "termos_confusos": termos_confusos,
            "suporte_estilos": suporte_estilos,
            "gostos_plataforma": gostos_plataforma,
            "desafios": desafios,
            "sugestao_funcionalidade": sugestao_funcionalidade,
            "recomendacao": recomendacao,
            "outras_sugestoes": outras_sugestoes
        }
        # Armazenar em sessão (ou enviar para backend)
        if 'avaliacoes' not in st.session_state:
            st.session_state['avaliacoes'] = []

        st.session_state['avaliacoes'].append(resposta)
        st.success("✅ Avaliação registrada! Envie suas respostas seguindo as instruções abaixo.")

        # Opção de baixar CSV com todas respostas
        df_avaliacoes = pd.DataFrame(st.session_state['avaliacoes'])
        st.download_button(
            label="📥 Baixar todas respostas (CSV)",
            data=df_avaliacoes.to_csv(index=False),
            file_name="avaliacoes_plataforma.csv",
            mime="text/csv"
        )
        st.markdown("""
        ---
        ### 📧 Enviar respostas por e-mail
        Para nos enviar sua avaliação:

        1. Clique no botão acima para baixar suas respostas em **CSV**.
        2. Envie o arquivo por e-mail para: **marianaandreotti@gmail.com** (Mariana Dias).
        3. No corpo do e-mail, sinta-se à vontade para adicionar comentários adicionais.
        
        💡 Sugestão de assunto do e-mail: "Meu Nome:Avaliação Plataforma Clima Urbano Interativo"
        """)

