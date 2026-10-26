# """
# Rule-based pre-processing and override layer that sits in front of the
# CNN sentiment model.

# Pipeline: translate -> normalize -> clean -> (emoji / idiom / negated-
# adjective / hedge / contrast-clause / VADER overrides) -> CNN fallback.

# This replaces the old hand-built POSITIVE_WORDS / NEGATIVE_WORDS /
# NEUTRAL_WORDS dictionaries with VADER (a pretrained rule-based
# sentiment analyzer, extended with a small product-review domain
# lexicon below). VADER already understands negation ("not bad") and
# intensifiers ("very good"), so a custom negation-span tracker is not
# needed either.

# Public API used by the rest of the app (see model_registry.CNNModel):
#     resolve_sentiment(raw_review) -> (label_or_None, cleaned_text)
#         `label_or_None` is "Positive" / "Negative" / "Neutral" if a
#         rule fired confidently, or None if the CNN should decide.
#         `cleaned_text` is always returned (translated, lowercased,
#         stopwords removed) so the caller can feed it to the CNN when
#         `label_or_None` is None.

# Install:
#     pip install deep-translator contractions emoji nltk vaderSentiment
# """
# import logging
# import re

# import contractions
# import emoji
# import nltk
# from nltk.corpus import stopwords
# from deep_translator import GoogleTranslator
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# logger = logging.getLogger(__name__)

# try:
#     stopwords.words("english")
# except LookupError:
#     nltk.download("stopwords")


# # =========================================================
# # STEP 0: PURE-EMOJI OVERRIDE
# # If a review has no letters at all, score it straight from an emoji
# # lookup table before translation/cleaning/VADER/the CNN ever see it.
# # =========================================================
# POSITIVE_EMOJI = {
#     "😀", "😃", "😄", "😁", "😆", "😊", "🙂", "😉", "😍", "🥰", "😘", "😗",
#     "😙", "😚", "🤩", "😇", "🥳", "👍", "👏", "💯", "🔥", "❤️", "❤", "💕",
#     "💖", "💗", "💓", "💞", "💘", "💝", "✨", "🎉", "🙌", "👌", "💪", "😻",
#     "🥇", "👑",
# }
# NEGATIVE_EMOJI = {
#     "😢", "😭", "😡", "😠", "🤬", "😞", "😔", "😟", "😕", "☹️", "☹", "😣",
#     "😖", "😩", "😫", "😤", "👎", "💔", "🤢", "🤮", "😱", "😨", "😰", "😥",
#     "😓", "🙁", "😑", "💩", "😒", "😪",
# }
# NEUTRAL_EMOJI = {
#     "😐", "😶", "🤷", "🤔", "😴", "😬", "🙄", "😯", "😦", "😧", "🫤",
# }


# def pure_emoji_sentiment(raw_text):
#     """Return a label if raw_text is emoji-only and recognized, else None."""
#     if not isinstance(raw_text, str) or not raw_text.strip():
#         return None
#     if any(ch.isalpha() for ch in raw_text):
#         return None

#     pos = sum(raw_text.count(e) for e in POSITIVE_EMOJI)
#     neg = sum(raw_text.count(e) for e in NEGATIVE_EMOJI)
#     neu = sum(raw_text.count(e) for e in NEUTRAL_EMOJI)

#     if pos == neg == neu == 0:
#         return None
#     if pos > neg and pos > neu:
#         return "Positive"
#     if neg > pos and neg > neu:
#         return "Negative"
#     return "Neutral"


# # =========================================================
# # STEP 1: TRANSLATE
# # =========================================================
# _translator = GoogleTranslator(source="auto", target="en")


# def translate_to_english(text):
#     if text is None or str(text).strip() == "":
#         return text
#     text_str = str(text)
#     if not any(ch.isalpha() for ch in text_str):
#         return text_str
#     try:
#         result = _translator.translate(text_str)
#         return result if result and str(result).strip() else text_str
#     except Exception as e:
#         logger.warning("translate failed, using original text: %s", e)
#         return text_str


# # =========================================================
# # SMART-PUNCTUATION NORMALIZATION
# # Curly apostrophes/quotes ('' "") from phones/Word break negation
# # handling: both VADER's negation-word list and `contractions` key off
# # the straight ASCII apostrophe ('), so "wouldn't" with a curly quote
# # is silently NOT recognized as a negation. Normalize before anything
# # else touches the text.
# # =========================================================
# _SMART_PUNCT_MAP = {
#     "\u2018": "'", "\u2019": "'",
#     "\u201c": '"', "\u201d": '"',
#     "\u2032": "'", "\u2033": '"',
# }
# _smart_punct_pattern = re.compile("|".join(re.escape(k) for k in _SMART_PUNCT_MAP))


# def normalize_smart_punctuation(text):
#     if not isinstance(text, str):
#         return text
#     return _smart_punct_pattern.sub(lambda m: _SMART_PUNCT_MAP[m.group()], text)


# # =========================================================
# # HASHTAG EXPANSION
# # =========================================================
# _camel_boundary = re.compile(r'(?<!^)(?=[A-Z])')


# def expand_hashtags(text):
#     """'#PoorQuality #RegretBuy' -> 'Poor Quality Regret Buy'."""
#     def _split_tag(m):
#         parts = [p for p in _camel_boundary.split(m.group(1)) if p]
#         return " " + " ".join(parts)
#     return re.sub(r"#(\w+)", _split_tag, text)


# # =========================================================
# # EMOJI STRIPPING  (right before VADER/mixed-sentiment scoring)
# # VADER scores emoji by *typical* usage, which is often wrong in
# # context (e.g. money-with-wings read as "treat yourself" instead of
# # "money wasted" in "Not worth the price 💸"). Emoji-only text is
# # still handled correctly by pure_emoji_sentiment() earlier; this only
# # stops a stray emoji from overriding word-based scoring on mixed text.
# # =========================================================
# def _strip_emoji(text):
#     if not isinstance(text, str):
#         return text
#     return emoji.replace_emoji(text, replace="")


# # =========================================================
# # STEP 2: CLEAN  (what the CNN sees)
# # =========================================================
# _stop_words = set(stopwords.words("english"))
# _negation_words = {
#     "not", "no", "nor", "never", "none", "nobody",
#     "nothing", "neither", "without", "cannot",
# }
# _stop_words_keep_negation = _stop_words - _negation_words


# def _early_clean(text):
#     if not isinstance(text, str):
#         return ""
#     text = text.lower()
#     try:
#         text = contractions.fix(text)
#     except Exception:
#         pass
#     text = emoji.demojize(text, delimiters=(" ", " "))
#     text = re.sub(r"http\S+|www\S+", " ", text)
#     text = re.sub(r"@\w+", " ", text)
#     text = re.sub(r"#", " ", text)
#     return text


# def _finish_clean(text):
#     text = re.sub(r"[^a-zA-Z0-9\s!?']", " ", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     text = re.sub(r"(.)\1{2,}", r"\1\1", text)
#     return text


# def _remove_stopwords(text):
#     words = text.split()
#     return " ".join(w for w in words if w.lower() not in _stop_words_keep_negation)


# def clean_text(text):
#     """Full cleaning fed to the CNN."""
#     return _remove_stopwords(_finish_clean(_early_clean(text)))


# # =========================================================
# # DOMINANT-CLAUSE EXTRACTION
# # For each sentence, keep only the text after its last contrastive
# # conjunction ("comfortable but the color was flashy" -> "the color
# # was flashy" -- usually the reviewer's real verdict). Sentences are
# # rejoined with ". " so boundaries survive for per-sentence scoring.
# # =========================================================
# CONTRAST_WORDS = {"but", "however", "although", "though", "yet", "nonetheless"}
# _contrast_pattern = re.compile(r"\b(" + "|".join(CONTRAST_WORDS) + r")\b", re.IGNORECASE)
# _sentence_split_pattern = re.compile(r"[.!?]+")


# def dominant_text(text):
#     sentences = _sentence_split_pattern.split(text)
#     kept = []
#     for sent in sentences:
#         sent = sent.strip()
#         if not sent:
#             continue
#         matches = list(_contrast_pattern.finditer(sent))
#         kept.append(sent[matches[-1].end():].strip() if matches else sent)
#     return ". ".join(kept)


# def _split_sentences(text):
#     return [s.strip() for s in _sentence_split_pattern.split(text) if s.strip()]


# # =========================================================
# # CONTRAST-CLAUSE COUNTING
# # Guards against dominant_text() stripping every downside-half of a
# # multi-"but" review and stacking them into a falsely negative blob.
# # =========================================================
# MULTI_CONTRAST_THRESHOLD = 2
# _CONTRAST_CLAUSE_NEG_BAND = -0.05
# _CONTRAST_CLAUSE_STRONG_NEG_BAND = -0.3
# _POSITIVE_COUNTEREVIDENCE_BAND = 0.15


# def contrast_clause_count(text):
#     """How many contrastive conjunctions appear in the text at all."""
#     return len(_contrast_pattern.findall(text))


# def contrastive_negative_clause_count(text):
#     """(count, min_score): count of contrast markers whose follow-up
#     clause (up to the next sentence-ending punctuation) actually scores
#     negative with VADER -- as opposed to markers joining two positives
#     ("soft yet supportive") or resolving a concern positively ("but
#     worth every penny"). min_score is the most negative of those clause
#     scores, so one clearly negative clause can trigger the override on
#     its own without needing a second "but" elsewhere."""
#     count = 0
#     min_score = None
#     for m in _contrast_pattern.finditer(text):
#         after = text[m.end():]
#         clause = re.split(r"[.!?]", after, maxsplit=1)[0].strip().lstrip(",").strip()
#         if not clause:
#             continue
#         compound = _vader.polarity_scores(clause)["compound"]
#         if compound <= _CONTRAST_CLAUSE_NEG_BAND:
#             count += 1
#             if min_score is None or compound < min_score:
#                 min_score = compound
#     return count, min_score


# # =========================================================
# # HEDGE / LUKEWARM DETECTION
# # Several mild "okay/fine/average/decent" markers strung together read
# # as neutral to a human, but VADER's compound score is additive and
# # can sum them into a falsely confident verdict. Count hedge markers
# # directly and force Neutral before VADER runs.
# # =========================================================
# _HEDGE_PATTERNS = [
#     re.compile(r"\bokay\b", re.IGNORECASE),
#     re.compile(r"\bfine\b", re.IGNORECASE),
#     re.compile(r"\baverage\b", re.IGNORECASE),
#     re.compile(r"\bdecent\b", re.IGNORECASE),
#     re.compile(r"\balright\b", re.IGNORECASE),
#     re.compile(r"\bso-?so\b", re.IGNORECASE),
#     re.compile(r"\bmediocre\b", re.IGNORECASE),
#     re.compile(r"\bnothing (?:too |very |particularly )?(?:special|impressive|exciting)\b", re.IGNORECASE),
#     re.compile(r"\bnot (?:too |that )?(?:terrible|bad|great)\b", re.IGNORECASE),
#     re.compile(r"\bjust a regular\b", re.IGNORECASE),
#     re.compile(r"\b(?:just|pretty much) (?:okay|fine|average|decent)\b", re.IGNORECASE),
# ]
# HEDGE_COUNT_THRESHOLD = 3


# def hedge_marker_count(text):
#     return sum(1 for pattern in _HEDGE_PATTERNS if pattern.search(text))


# def hedge_override(text):
#     if hedge_marker_count(text) >= HEDGE_COUNT_THRESHOLD:
#         return "Neutral"
#     return None


# # =========================================================
# # IDIOM OVERRIDE  (checked before VADER)
# # Comparative-regret idioms like "could have been better" trip up any
# # word-scoring tool -- the word "better" alone looks positive, so the
# # idiom's real (mildly negative) meaning gets missed. Matched directly
# # with regex since these are common and few.
# # =========================================================
# IDIOM_PATTERNS = [
#     (re.compile(r"\bcould(?:'ve| have) been better\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bcould be better\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bnot the best\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bseen better days\b", re.IGNORECASE), "Negative"),
#     (re.compile(r"\bnothing special\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bnot great\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bleft (?:a lot|much) to be desired\b", re.IGNORECASE), "Negative"),
#     (re.compile(r"\bfar from perfect\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bnothing special\b.*\bbut\b.*\bdon'?t disappoint\b", re.IGNORECASE), "Neutral"),
#     (re.compile(r"\bnot worth (?:the )?(?:price|money|it|hype|wait|cost)\b", re.IGNORECASE), "Negative"),
# ]


# def idiom_override(text):
#     if not text:
#         return None
#     for pattern, label in IDIOM_PATTERNS:
#         if pattern.search(text):
#             return label
#     return None


# # =========================================================
# # NEGATED-ADJECTIVE OVERRIDE
# # VADER only dampens (rather than flips) a negated word's valence, and
# # its compound formula compresses short one-adjective texts well below
# # the confidence threshold ("not good" ~ -0.34, "not bad" ~ +0.43,
# # "not satisfied" ~ 0.00). Match the negation directly instead.
# # =========================================================
# _NEGATION_TRIGGER = (
#     r"(?:not|never|no|isn't|isnt|wasn't|wasnt|aren't|arent|weren't|werent|"
#     r"didn't|didnt|doesn't|doesnt|don't|dont|couldn't|couldnt|"
#     r"wouldn't|wouldnt|shouldn't|shouldnt)"
# )

# # Positive on their own -> negating them is a real complaint.
# _NEGATED_POSITIVE_WORDS = [
#     "good", "great", "impressive", "impressed", "satisfied", "satisfying",
#     "happy", "pleased", "comfortable", "durable", "recommend", "recommended",
#     "amazing", "excellent", "worth", "helpful", "useful",
# ]
# # Negative on their own -> negating them is litotes ("not bad" = mildly
# # positive/lukewarm, so Neutral rather than a confident Positive).
# _NEGATED_NEGATIVE_WORDS = [
#     "bad", "terrible", "awful", "horrible", "poor", "disappointing",
#     "disappointed", "flimsy", "cheap", "useless",
# ]

# # Allow up to 2 filler words between negation and adjective ("not that
# # good", "wasn't really satisfied").
# _negated_positive_pattern = re.compile(
#     rf"\b{_NEGATION_TRIGGER}\b(?:\s+\w+){{0,2}}\s+(?:{'|'.join(_NEGATED_POSITIVE_WORDS)})\b",
#     re.IGNORECASE,
# )
# _negated_negative_pattern = re.compile(
#     rf"\b{_NEGATION_TRIGGER}\b(?:\s+\w+){{0,2}}\s+(?:{'|'.join(_NEGATED_NEGATIVE_WORDS)})\b",
#     re.IGNORECASE,
# )


# def negated_adjective_override(text):
#     """Only fires when exactly one direction matches, so genuinely
#     mixed text ('not bad but not great either') is left for the rest
#     of the pipeline to sort out."""
#     if not text:
#         return None
#     neg_pos = _negated_positive_pattern.search(text)
#     neg_neg = _negated_negative_pattern.search(text)
#     if neg_pos and not neg_neg:
#         return "Negative"
#     if neg_neg and not neg_pos:
#         return "Positive"  # litotes: lukewarm, not a strong Positive
#     return None


# # =========================================================
# # VADER + DOMAIN LEXICON
# # VADER's built-in lexicon is tuned for social media / 2014-era Amazon
# # comments and has real gaps for product-quality vocabulary ("flimsy",
# # "fraying", "peeling" score exactly 0.0 -- not weak, absent). Extend
# # it additively (never overrides an existing word) with common
# # product-review terms on VADER's own -4..+4 scale.
# # =========================================================
# _vader = SentimentIntensityAnalyzer()

# _DOMAIN_LEXICON = {
#     # durability / quality complaints
#     "flimsy": -2.0, "fraying": -1.8, "frayed": -1.8, "fray": -1.5,
#     "peeling": -1.8, "peeled": -1.8, "cracking": -1.8, "cracked": -2.0,
#     "chipping": -1.6, "chipped": -1.8, "wobbly": -1.6, "squeaky": -1.2,
#     "leaking": -2.0, "leaks": -1.8, "defective": -2.8, "malfunctioning": -2.6,
#     "snapped": -2.0, "jammed": -1.8, "faded": -1.4, "fading": -1.2,
#     "pilling": -1.4, "shedding": -1.2, "discolored": -1.6, "stained": -1.4,
#     "warped": -1.6, "itchy": -1.2, "scratchy": -1.4, "questionable": -1.8,
#     "rusting": -2.0, "rusted": -2.0, "rust": -1.8, "tarnished": -1.8,
#     "tarnishing": -1.6, "corroded": -2.2, "brittle": -1.8, "unravel": -1.8,
#     "unraveling": -1.8, "loosening": -1.2, "detached": -1.8, "splitting": -1.8,
#     # durability / quality praise
#     "durable": 2.0, "sturdy": 2.0, "breathable": 1.6, "snug": 1.4,
#     "cozy": 1.8, "stylish": 1.8, "sleek": 1.6, "compact": 1.2,
#     "trendy": 1.6, "versatile": 1.6, "lightweight": 1.4, "seamless": 1.6,
#     "plush": 1.8, "silky": 1.6,
#     # skin reaction / allergic complaints
#     "rash": -2.2, "rashes": -2.2, "irritation": -1.8, "irritated": -1.8,
#     "itching": -1.6, "allergic": -1.8, "allergy": -1.6, "breakout": -1.6,
#     "hives": -2.4, "swelling": -1.8, "swollen": -1.8, "inflamed": -1.8,
#     "inflammation": -1.8, "redness": -1.4, "blister": -2.0, "blisters": -2.0,
#     "burning": -1.6, "chafing": -1.8, "chafe": -1.6, "sweaty": -1.0,
#     "stuffy": -1.0, "suffocating": -2.0, "comfy": 1.8, "numbness": -1.6,
#     "blistering": -2.0,
#     # fit & sizing
#     "tight": -1.0, "loose": -0.8, "baggy": -0.6, "undersized": -1.6, "roomy": 1.0,
#     # material / fabric quality
#     "rough": -1.2, "coarse": -1.0, "stiff": -1.0, "rigid": -0.8,
#     "flexible": 1.2, "stretchy": 1.0, "premium": 2.0, "luxurious": 2.2,
#     "authentic": 1.4, "fake": -2.2, "counterfeit": -2.4, "knockoff": -2.0,
#     # footwear-specific
#     "slippery": -1.6, "supportive": 1.6, "cushioned": 1.6, "cushioning": 1.4,
#     "pinches": -1.8, "pinching": -1.8, "rubbing": -1.4,
#     # accessories-specific
#     "tangled": -1.4, "tangles": -1.4, "bulky": -1.4, "dainty": 1.2,
#     "elegant": 2.0, "classy": 1.8,
#     # odor / smell
#     "smelly": -1.8, "odor": -1.4, "stink": -2.0, "stinky": -1.8,
#     # sound
#     "creaky": -1.4, "noisy": -1.2,
#     # aesthetic / style
#     "gorgeous": 2.6, "stunning": 2.6, "chic": 1.8, "dull": -1.4,
#     "outdated": -1.4, "gaudy": -1.6, "tacky": -1.8,
#     # functionality / fastenings
#     "stuck": -1.4, "functional": 1.2, "reliable": 1.8, "unreliable": -1.8,
#     # price / value perception
#     "overpriced": -1.8, "pricey": -1.0, "affordable": 1.4, "bargain": 1.6,
#     "ripoff": -2.4,
# }
# _vader.lexicon.update(_DOMAIN_LEXICON)

# VADER_POS_THRESHOLD = 0.5
# VADER_NEG_THRESHOLD = -0.5
# VADER_NEUTRAL_BAND = 0.05

# _word_pattern = re.compile(r"[a-zA-Z']+")


# def _adaptive_thresholds(text):
#     """VADER's compound = sum / sqrt(sum^2 + 15); the '+15' constant is
#     tuned for multi-word text, so a short review (1-4 content words)
#     can't reach +/-0.5 even with one clear, unambiguous verdict word.
#     Loosen the threshold as word count drops."""
#     word_count = len(_word_pattern.findall(text))
#     if word_count <= 4:
#         return 0.15, -0.15
#     if word_count <= 8:
#         return 0.3, -0.3
#     return VADER_POS_THRESHOLD, VADER_NEG_THRESHOLD


# def vader_override(text):
#     """Positive/Negative/Neutral only when VADER's compound score is
#     clearly on one side or clearly neutral. Mixed/weak text -> None,
#     letting the CNN decide."""
#     scores = _vader.polarity_scores(text)
#     compound = scores["compound"]
#     pos_threshold, neg_threshold = _adaptive_thresholds(text)

#     if compound >= pos_threshold:
#         return "Positive"
#     if compound <= neg_threshold:
#         return "Negative"
#     if abs(compound) <= VADER_NEUTRAL_BAND:
#         return "Neutral"
#     return None


# def vader_paragraph_override(text):
#     """Score each sentence independently instead of the whole blob at
#     once (VADER's compound is closer to a normalized sum, so several
#     mildly-valenced sentences can otherwise accumulate into a falsely
#     confident verdict). Only return a confident label if the average
#     clears the threshold AND no sentence disagrees, or if every
#     sentence unanimously agrees on a side even without clearing the
#     average threshold."""
#     sentences = _split_sentences(text)
#     if len(sentences) <= 1:
#         return vader_override(text)

#     compounds = [_vader.polarity_scores(s)["compound"] for s in sentences]
#     avg = sum(compounds) / len(compounds)

#     if avg >= VADER_POS_THRESHOLD:
#         return None if any(c <= VADER_NEG_THRESHOLD for c in compounds) else "Positive"
#     if avg <= VADER_NEG_THRESHOLD:
#         return None if any(c >= VADER_POS_THRESHOLD for c in compounds) else "Negative"
#     if abs(avg) <= VADER_NEUTRAL_BAND:
#         return "Neutral"

#     if all(c <= _CONTRAST_CLAUSE_NEG_BAND for c in compounds) and avg <= _CONTRAST_CLAUSE_STRONG_NEG_BAND:
#         return "Negative"
#     if all(c >= -_CONTRAST_CLAUSE_NEG_BAND for c in compounds) and avg >= -_CONTRAST_CLAUSE_STRONG_NEG_BAND:
#         return "Positive"
#     return None


# def has_mixed_sentiment(text, strong_threshold=2.5):
#     """True if text has at least one word VADER rates strongly
#     positive AND one rated strongly negative ('love' +3.2, 'hate'
#     -2.7) -- checked word-by-word so one strong word can't cancel the
#     other and hide a genuinely mixed opinion."""
#     words = _word_pattern.findall(text.lower())
#     saw_pos = any(_vader.lexicon.get(w, 0) >= strong_threshold for w in words)
#     saw_neg = any(_vader.lexicon.get(w, 0) <= -strong_threshold for w in words)
#     return saw_pos and saw_neg


# # =========================================================
# # PUBLIC ENTRY POINT
# # =========================================================
# def resolve_sentiment(raw_review: str):
#     """Run the full rule-based pipeline against raw_review.

#     Returns (label, cleaned_text):
#       label        -- "Positive" / "Negative" / "Neutral" if a rule
#                        fired confidently, else None (let the CNN decide).
#       cleaned_text -- translated + cleaned text, ready for the CNN's
#                        tokenizer, regardless of whether label is None.
#     """
#     emoji_verdict = pure_emoji_sentiment(raw_review)
#     if emoji_verdict is not None:
#         return emoji_verdict, clean_text(raw_review)

#     translated = translate_to_english(raw_review)
#     translated = normalize_smart_punctuation(translated)
#     translated = expand_hashtags(translated)

#     cleaned = clean_text(translated)
#     dominant = dominant_text(translated)
#     dominant_no_emoji = _strip_emoji(dominant)

#     # Idioms are checked against the untouched `translated` text first:
#     # dominant_text() can strip away the clause containing the idiom
#     # (e.g. "Nothing special, but they don't disappoint either" drops
#     # "Nothing special" because of the "but"). Falling back to
#     # `dominant` still covers the cases that need it.
#     idiom = idiom_override(translated) or idiom_override(dominant)
#     if idiom is not None:
#         return idiom, cleaned

#     negated = negated_adjective_override(translated) or negated_adjective_override(dominant)
#     if negated is not None:
#         return negated, cleaned

#     hedge = hedge_override(dominant_no_emoji)
#     if hedge is not None:
#         return hedge, cleaned

#     contrast_count = contrast_clause_count(translated)
#     negative_contrast_count, negative_contrast_min_score = contrastive_negative_clause_count(translated)

#     multi_contrast_fires = negative_contrast_count >= MULTI_CONTRAST_THRESHOLD
#     single_strong_contrast_fires = (
#         negative_contrast_count >= 1
#         and negative_contrast_min_score is not None
#         and negative_contrast_min_score <= _CONTRAST_CLAUSE_STRONG_NEG_BAND
#     )

#     # Only treat a flagged negative contrast clause as a genuine MIXED
#     # review if the rest of the text still has positive content to
#     # balance against -- otherwise a uniformly negative review gets
#     # misread as "mixed" just for containing the word "but".
#     has_positive_counterevidence = any(
#         _vader.polarity_scores(s)["compound"] > _POSITIVE_COUNTEREVIDENCE_BAND
#         for s in _split_sentences(dominant_no_emoji)
#     )

#     if (multi_contrast_fires or single_strong_contrast_fires) and has_positive_counterevidence:
#         return "Neutral", cleaned

#     if contrast_count <= 1:
#         if has_mixed_sentiment(dominant_no_emoji):
#             return "Neutral", cleaned

#         override = vader_paragraph_override(dominant_no_emoji)
#         if override is not None:
#             return override, cleaned

#     if cleaned.strip() == "":
#         return "Neutral", cleaned

#     return None, cleaned


# def fallback_sentiment(text: str):
#     """Classify text without TensorFlow for low-memory deployments."""
#     compound = _vader.polarity_scores(text)["compound"]
#     if compound >= 0.05:
#         label = "Positive"
#     elif compound <= -0.05:
#         label = "Negative"
#     else:
#         label = "Neutral"

#     strength = min(abs(compound), 1.0)
#     confidence = strength if label != "Neutral" else 1.0 - strength
#     probabilities = {
#         "Positive": 0.0,
#         "Neutral": 0.0,
#         "Negative": 0.0,
#     }
#     probabilities[label] = confidence
#     remaining = 1.0 - confidence
#     other_labels = [name for name in probabilities if name != label]
#     for name in other_labels:
#         probabilities[name] = remaining / len(other_labels)
#     return label, confidence, probabilities





"""
Rule-based pre-processing and override layer that sits in front of the
CNN sentiment model.

Pipeline: translate -> normalize -> clean -> (emoji / idiom / negated-
adjective / hedge / contrast-clause / VADER overrides) -> CNN fallback.

This replaces the old hand-built POSITIVE_WORDS / NEGATIVE_WORDS /
NEUTRAL_WORDS dictionaries with VADER (a pretrained rule-based
sentiment analyzer, extended with a small product-review domain
lexicon below). VADER already understands negation ("not bad") and
intensifiers ("very good"), so a custom negation-span tracker is not
needed either.

Public API used by the rest of the app (see model_registry.CNNModel):
    resolve_sentiment(raw_review) -> (label_or_None, cleaned_text)
        `label_or_None` is "Positive" / "Negative" / "Neutral" if a
        rule fired confidently, or None if the CNN should decide.
        `cleaned_text` is always returned (translated, lowercased,
        stopwords removed) so the caller can feed it to the CNN when
        `label_or_None` is None.

Install:
    pip install deep-translator contractions emoji nltk vaderSentiment
"""
import logging
import re

import contractions
import emoji
import nltk
from nltk.corpus import stopwords
from deep_translator import GoogleTranslator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")


# =========================================================
# STEP 0: PURE-EMOJI OVERRIDE
# If a review has no letters at all, score it straight from an emoji
# lookup table before translation/cleaning/VADER/the CNN ever see it.
# =========================================================
POSITIVE_EMOJI = {
    "😀", "😃", "😄", "😁", "😆", "😊", "🙂", "😉", "😍", "🥰", "😘", "😗",
    "😙", "😚", "🤩", "😇", "🥳", "👍", "👏", "💯", "🔥", "❤️", "❤", "💕",
    "💖", "💗", "💓", "💞", "💘", "💝", "✨", "🎉", "🙌", "👌", "💪", "😻",
    "🥇", "👑",
}
NEGATIVE_EMOJI = {
    "😢", "😭", "😡", "😠", "🤬", "😞", "😔", "😟", "😕", "☹️", "☹", "😣",
    "😖", "😩", "😫", "😤", "👎", "💔", "🤢", "🤮", "😱", "😨", "😰", "😥",
    "😓", "🙁", "😑", "💩", "😒", "😪",
}
NEUTRAL_EMOJI = {
    "😐", "😶", "🤷", "🤔", "😴", "😬", "🙄", "😯", "😦", "😧", "🫤",
}


def pure_emoji_sentiment(raw_text):
    """Return a label if raw_text is emoji-only and recognized, else None."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None
    if any(ch.isalpha() for ch in raw_text):
        return None

    pos = sum(raw_text.count(e) for e in POSITIVE_EMOJI)
    neg = sum(raw_text.count(e) for e in NEGATIVE_EMOJI)
    neu = sum(raw_text.count(e) for e in NEUTRAL_EMOJI)

    if pos == neg == neu == 0:
        return None
    if pos > neg and pos > neu:
        return "Positive"
    if neg > pos and neg > neu:
        return "Negative"
    return "Neutral"


# =========================================================
# STEP 1: TRANSLATE
# =========================================================
_translator = GoogleTranslator(source="auto", target="en")


def translate_to_english(text):
    if text is None or str(text).strip() == "":
        return text
    text_str = str(text)
    if not any(ch.isalpha() for ch in text_str):
        return text_str
    try:
        result = _translator.translate(text_str)
        return result if result and str(result).strip() else text_str
    except Exception as e:
        logger.warning("translate failed, using original text: %s", e)
        return text_str


# =========================================================
# SMART-PUNCTUATION NORMALIZATION
# Curly apostrophes/quotes ('' "") from phones/Word break negation
# handling: both VADER's negation-word list and `contractions` key off
# the straight ASCII apostrophe ('), so "wouldn't" with a curly quote
# is silently NOT recognized as a negation. Normalize before anything
# else touches the text.
# =========================================================
_SMART_PUNCT_MAP = {
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2032": "'", "\u2033": '"',
}
_smart_punct_pattern = re.compile("|".join(re.escape(k) for k in _SMART_PUNCT_MAP))


def normalize_smart_punctuation(text):
    if not isinstance(text, str):
        return text
    return _smart_punct_pattern.sub(lambda m: _SMART_PUNCT_MAP[m.group()], text)


# =========================================================
# HASHTAG EXPANSION
# =========================================================
_camel_boundary = re.compile(r'(?<!^)(?=[A-Z])')


def expand_hashtags(text):
    """'#PoorQuality #RegretBuy' -> 'Poor Quality Regret Buy'."""
    def _split_tag(m):
        parts = [p for p in _camel_boundary.split(m.group(1)) if p]
        return " " + " ".join(parts)
    return re.sub(r"#(\w+)", _split_tag, text)


# =========================================================
# EMOJI STRIPPING  (right before VADER/mixed-sentiment scoring)
# VADER scores emoji by *typical* usage, which is often wrong in
# context (e.g. money-with-wings read as "treat yourself" instead of
# "money wasted" in "Not worth the price 💸"). Emoji-only text is
# still handled correctly by pure_emoji_sentiment() earlier; this only
# stops a stray emoji from overriding word-based scoring on mixed text.
# =========================================================
def _strip_emoji(text):
    if not isinstance(text, str):
        return text
    return emoji.replace_emoji(text, replace="")


# =========================================================
# STEP 2: CLEAN  (what the CNN sees)
# =========================================================
_stop_words = set(stopwords.words("english"))
_negation_words = {
    "not", "no", "nor", "never", "none", "nobody",
    "nothing", "neither", "without", "cannot",
}
_stop_words_keep_negation = _stop_words - _negation_words


def _early_clean(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    try:
        text = contractions.fix(text)
    except Exception:
        pass
    text = emoji.demojize(text, delimiters=(" ", " "))
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#", " ", text)
    return text


def _finish_clean(text):
    text = re.sub(r"[^a-zA-Z0-9\s!?']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return text


def _remove_stopwords(text):
    words = text.split()
    return " ".join(w for w in words if w.lower() not in _stop_words_keep_negation)


def clean_text(text):
    """Full cleaning fed to the CNN."""
    return _remove_stopwords(_finish_clean(_early_clean(text)))


# =========================================================
# DOMINANT-CLAUSE EXTRACTION
# For each sentence, keep only the text after its last contrastive
# conjunction ("comfortable but the color was flashy" -> "the color
# was flashy" -- usually the reviewer's real verdict). Sentences are
# rejoined with ". " so boundaries survive for per-sentence scoring.
# =========================================================
CONTRAST_WORDS = {"but", "however", "although", "though", "yet", "nonetheless"}
_contrast_pattern = re.compile(r"\b(" + "|".join(CONTRAST_WORDS) + r")\b", re.IGNORECASE)
_sentence_split_pattern = re.compile(r"[.!?]+")


def dominant_text(text):
    sentences = _sentence_split_pattern.split(text)
    kept = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        matches = list(_contrast_pattern.finditer(sent))
        kept.append(sent[matches[-1].end():].strip() if matches else sent)
    return ". ".join(kept)


def _split_sentences(text):
    return [s.strip() for s in _sentence_split_pattern.split(text) if s.strip()]


# =========================================================
# CONTRAST-CLAUSE COUNTING
# Guards against dominant_text() stripping every downside-half of a
# multi-"but" review and stacking them into a falsely negative blob.
# =========================================================
MULTI_CONTRAST_THRESHOLD = 2
_CONTRAST_CLAUSE_NEG_BAND = -0.05
_CONTRAST_CLAUSE_STRONG_NEG_BAND = -0.3
_POSITIVE_COUNTEREVIDENCE_BAND = 0.15


def contrast_clause_count(text):
    """How many contrastive conjunctions appear in the text at all."""
    return len(_contrast_pattern.findall(text))


def contrastive_negative_clause_count(text):
    """(count, min_score): count of contrast markers whose follow-up
    clause (up to the next sentence-ending punctuation) actually scores
    negative with VADER -- as opposed to markers joining two positives
    ("soft yet supportive") or resolving a concern positively ("but
    worth every penny"). min_score is the most negative of those clause
    scores, so one clearly negative clause can trigger the override on
    its own without needing a second "but" elsewhere."""
    count = 0
    min_score = None
    for m in _contrast_pattern.finditer(text):
        after = text[m.end():]
        clause = re.split(r"[.!?]", after, maxsplit=1)[0].strip().lstrip(",").strip()
        if not clause:
            continue
        compound = _vader.polarity_scores(clause)["compound"]
        if compound <= _CONTRAST_CLAUSE_NEG_BAND:
            count += 1
            if min_score is None or compound < min_score:
                min_score = compound
    return count, min_score


# =========================================================
# HEDGE / LUKEWARM DETECTION
# Several mild "okay/fine/average/decent" markers strung together read
# as neutral to a human, but VADER's compound score is additive and
# can sum them into a falsely confident verdict. Count hedge markers
# directly and force Neutral before VADER runs.
# =========================================================
_HEDGE_PATTERNS = [
    re.compile(r"\bokay\b", re.IGNORECASE),
    re.compile(r"\bfine\b", re.IGNORECASE),
    re.compile(r"\baverage\b", re.IGNORECASE),
    re.compile(r"\bdecent\b", re.IGNORECASE),
    re.compile(r"\balright\b", re.IGNORECASE),
    re.compile(r"\bso-?so\b", re.IGNORECASE),
    re.compile(r"\bmediocre\b", re.IGNORECASE),
    re.compile(r"\bnothing (?:too |very |particularly )?(?:special|impressive|exciting)\b", re.IGNORECASE),
    re.compile(r"\bnot (?:too |that |so |very |all that |that much )?(?:terrible|bad|great|good)\b", re.IGNORECASE),
    re.compile(r"\bjust a regular\b", re.IGNORECASE),
    re.compile(r"\b(?:just|pretty much) (?:okay|fine|average|decent)\b", re.IGNORECASE),
]
HEDGE_COUNT_THRESHOLD = 3


def hedge_marker_count(text):
    return sum(1 for pattern in _HEDGE_PATTERNS if pattern.search(text))


def hedge_override(text):
    if hedge_marker_count(text) >= HEDGE_COUNT_THRESHOLD:
        return "Neutral"
    return None


# =========================================================
# IDIOM OVERRIDE  (checked before VADER)
# Comparative-regret idioms like "could have been better" trip up any
# word-scoring tool -- the word "better" alone looks positive, so the
# idiom's real (mildly negative) meaning gets missed. Matched directly
# with regex since these are common and few.
# =========================================================
IDIOM_PATTERNS = [
    (re.compile(r"\bcould(?:'ve| have) been better\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bcould be better\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bnot the best\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bseen better days\b", re.IGNORECASE), "Negative"),
    (re.compile(r"\bnothing special\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bnot great\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bleft (?:a lot|much) to be desired\b", re.IGNORECASE), "Negative"),
    (re.compile(r"\bfar from perfect\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bnothing special\b.*\bbut\b.*\bdon'?t disappoint\b", re.IGNORECASE), "Neutral"),
    (re.compile(r"\bnot worth (?:the )?(?:price|money|it|hype|wait|cost)\b", re.IGNORECASE), "Negative"),
]


def idiom_override(text):
    if not text:
        return None
    for pattern, label in IDIOM_PATTERNS:
        if pattern.search(text):
            return label
    return None


# =========================================================
# NEGATED-ADJECTIVE OVERRIDE
# VADER only dampens (rather than flips) a negated word's valence, and
# its compound formula compresses short one-adjective texts well below
# the confidence threshold ("not good" ~ -0.34, "not bad" ~ +0.43,
# "not satisfied" ~ 0.00). Match the negation directly instead.
# =========================================================
_NEGATION_TRIGGER = (
    r"(?:not|never|no|isn't|isnt|wasn't|wasnt|aren't|arent|weren't|werent|"
    r"didn't|didnt|doesn't|doesnt|don't|dont|couldn't|couldnt|"
    r"wouldn't|wouldnt|shouldn't|shouldnt)"
)

# Positive on their own -> negating them is a real complaint.
_NEGATED_POSITIVE_WORDS = [
    "good", "great", "impressive", "impressed", "satisfied", "satisfying",
    "happy", "pleased", "comfortable", "durable", "recommend", "recommended",
    "amazing", "excellent", "worth", "helpful", "useful",
]
# Negative on their own -> negating them is litotes ("not bad" = mildly
# positive/lukewarm, so Neutral rather than a confident Positive).
_NEGATED_NEGATIVE_WORDS = [
    "bad", "terrible", "awful", "horrible", "poor", "disappointing",
    "disappointed", "flimsy", "cheap", "useless",
]

# Allow up to 3 filler words between negation and adjective ("not that
# much good", "wasn't really satisfied").
_negated_positive_pattern = re.compile(
    rf"\b{_NEGATION_TRIGGER}\b(?:\s+(?!(?:but|however|although|though|yet|nonetheless)\b)\w+){{0,3}}\s+(?:{'|'.join(_NEGATED_POSITIVE_WORDS)})\b",
    re.IGNORECASE,
)
_negated_negative_pattern = re.compile(
    rf"\b{_NEGATION_TRIGGER}\b(?:\s+(?!(?:but|however|although|though|yet|nonetheless)\b)\w+){{0,3}}\s+(?:{'|'.join(_NEGATED_NEGATIVE_WORDS)})\b",
    re.IGNORECASE,
)


def negated_adjective_override(text):
    """Only fires when exactly one direction matches, so genuinely
    mixed text ('not bad but not great either') is left for the rest
    of the pipeline to sort out."""
    if not text:
        return None
    neg_pos = _negated_positive_pattern.search(text)
    neg_neg = _negated_negative_pattern.search(text)
    if neg_pos and not neg_neg:
        return "Negative"
    if neg_neg and not neg_pos:
        return "Positive"  # litotes: lukewarm, not a strong Positive
    if neg_pos and neg_neg:
        # "not good, not bad" / "not that good, not so bad": the reviewer
        # is explicitly denying BOTH extremes -> the textbook Neutral.
        return "Neutral"
    return None


# =========================================================
# VADER + DOMAIN LEXICON
# VADER's built-in lexicon is tuned for social media / 2014-era Amazon
# comments and has real gaps for product-quality vocabulary ("flimsy",
# "fraying", "peeling" score exactly 0.0 -- not weak, absent). Extend
# it additively (never overrides an existing word) with common
# product-review terms on VADER's own -4..+4 scale.
# =========================================================
_vader = SentimentIntensityAnalyzer()

_DOMAIN_LEXICON = {
    # durability / quality complaints
    "flimsy": -2.0, "fraying": -1.8, "frayed": -1.8, "fray": -1.5,
    "peeling": -1.8, "peeled": -1.8, "cracking": -1.8, "cracked": -2.0,
    "chipping": -1.6, "chipped": -1.8, "wobbly": -1.6, "squeaky": -1.2,
    "leaking": -2.0, "leaks": -1.8, "defective": -2.8, "malfunctioning": -2.6,
    "snapped": -2.0, "jammed": -1.8, "faded": -1.4, "fading": -1.2,
    "pilling": -1.4, "shedding": -1.2, "discolored": -1.6, "stained": -1.4,
    "warped": -1.6, "itchy": -1.2, "scratchy": -1.4, "questionable": -1.8,
    "rusting": -2.0, "rusted": -2.0, "rust": -1.8, "tarnished": -1.8,
    "tarnishing": -1.6, "corroded": -2.2, "brittle": -1.8, "unravel": -1.8,
    "unraveling": -1.8, "loosening": -1.2, "detached": -1.8, "splitting": -1.8,
    # durability / quality praise
    "durable": 2.0, "sturdy": 2.0, "breathable": 1.6, "snug": 1.4,
    "cozy": 1.8, "stylish": 1.8, "sleek": 1.6, "compact": 1.2,
    "trendy": 1.6, "versatile": 1.6, "lightweight": 1.4, "seamless": 1.6,
    "plush": 1.8, "silky": 1.6,
    # skin reaction / allergic complaints
    "rash": -2.2, "rashes": -2.2, "irritation": -1.8, "irritated": -1.8,
    "itching": -1.6, "allergic": -1.8, "allergy": -1.6, "breakout": -1.6,
    "hives": -2.4, "swelling": -1.8, "swollen": -1.8, "inflamed": -1.8,
    "inflammation": -1.8, "redness": -1.4, "blister": -2.0, "blisters": -2.0,
    "burning": -1.6, "chafing": -1.8, "chafe": -1.6, "sweaty": -1.0,
    "stuffy": -1.0, "suffocating": -2.0, "comfy": 1.8, "numbness": -1.6,
    "blistering": -2.0,
    # fit & sizing
    "tight": -1.0, "loose": -0.8, "baggy": -0.6, "undersized": -1.6, "roomy": 1.0,
    # material / fabric quality
    "rough": -1.2, "coarse": -1.0, "stiff": -1.0, "rigid": -0.8,
    "flexible": 1.2, "stretchy": 1.0, "premium": 2.0, "luxurious": 2.2,
    "authentic": 1.4, "fake": -2.2, "counterfeit": -2.4, "knockoff": -2.0,
    # footwear-specific
    "slippery": -1.6, "supportive": 1.6, "cushioned": 1.6, "cushioning": 1.4,
    "pinches": -1.8, "pinching": -1.8, "rubbing": -1.4,
    # accessories-specific
    "tangled": -1.4, "tangles": -1.4, "bulky": -1.4, "dainty": 1.2,
    "elegant": 2.0, "classy": 1.8,
    # odor / smell
    "smelly": -1.8, "odor": -1.4, "stink": -2.0, "stinky": -1.8,
    # sound
    "creaky": -1.4, "noisy": -1.2,
    # aesthetic / style
    "gorgeous": 2.6, "stunning": 2.6, "chic": 1.8, "dull": -1.4,
    "outdated": -1.4, "gaudy": -1.6, "tacky": -1.8,
    # functionality / fastenings
    "stuck": -1.4, "functional": 1.2, "reliable": 1.8, "unreliable": -1.8,
    # price / value perception
    "overpriced": -1.8, "pricey": -1.0, "affordable": 1.4, "bargain": 1.6,
    "ripoff": -2.4,
}
_vader.lexicon.update(_DOMAIN_LEXICON)

VADER_POS_THRESHOLD = 0.5
VADER_NEG_THRESHOLD = -0.5
VADER_NEUTRAL_BAND = 0.05

_word_pattern = re.compile(r"[a-zA-Z']+")


def _adaptive_thresholds(text):
    """VADER's compound = sum / sqrt(sum^2 + 15); the '+15' constant is
    tuned for multi-word text, so a short review (1-4 content words)
    can't reach +/-0.5 even with one clear, unambiguous verdict word.
    Loosen the threshold as word count drops."""
    word_count = len(_word_pattern.findall(text))
    if word_count <= 4:
        return 0.15, -0.15
    if word_count <= 8:
        return 0.3, -0.3
    return VADER_POS_THRESHOLD, VADER_NEG_THRESHOLD


def vader_override(text):
    """Positive/Negative/Neutral only when VADER's compound score is
    clearly on one side or clearly neutral. Mixed/weak text -> None,
    letting the CNN decide."""
    scores = _vader.polarity_scores(text)
    compound = scores["compound"]
    pos_threshold, neg_threshold = _adaptive_thresholds(text)

    if compound >= pos_threshold:
        return "Positive"
    if compound <= neg_threshold:
        return "Negative"
    if abs(compound) <= VADER_NEUTRAL_BAND:
        return "Neutral"
    return None


def vader_paragraph_override(text):
    """Score each sentence independently instead of the whole blob at
    once (VADER's compound is closer to a normalized sum, so several
    mildly-valenced sentences can otherwise accumulate into a falsely
    confident verdict). Only return a confident label if the average
    clears the threshold AND no sentence disagrees, or if every
    sentence unanimously agrees on a side even without clearing the
    average threshold."""
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return vader_override(text)

    compounds = [_vader.polarity_scores(s)["compound"] for s in sentences]
    avg = sum(compounds) / len(compounds)

    if avg >= VADER_POS_THRESHOLD:
        return None if any(c <= VADER_NEG_THRESHOLD for c in compounds) else "Positive"
    if avg <= VADER_NEG_THRESHOLD:
        return None if any(c >= VADER_POS_THRESHOLD for c in compounds) else "Negative"
    if abs(avg) <= VADER_NEUTRAL_BAND:
        return "Neutral"

    if all(c <= _CONTRAST_CLAUSE_NEG_BAND for c in compounds) and avg <= _CONTRAST_CLAUSE_STRONG_NEG_BAND:
        return "Negative"
    if all(c >= -_CONTRAST_CLAUSE_NEG_BAND for c in compounds) and avg >= -_CONTRAST_CLAUSE_STRONG_NEG_BAND:
        return "Positive"
    return None


def has_mixed_sentiment(text, strong_threshold=2.5):
    """True if text has at least one word VADER rates strongly
    positive AND one rated strongly negative ('love' +3.2, 'hate'
    -2.7) -- checked word-by-word so one strong word can't cancel the
    other and hide a genuinely mixed opinion."""
    words = _word_pattern.findall(text.lower())
    saw_pos = any(_vader.lexicon.get(w, 0) >= strong_threshold for w in words)
    saw_neg = any(_vader.lexicon.get(w, 0) <= -strong_threshold for w in words)
    return saw_pos and saw_neg


# =========================================================
# PUBLIC ENTRY POINT
# =========================================================
def resolve_sentiment(raw_review: str):
    """Run the full rule-based pipeline against raw_review.

    Returns (label, cleaned_text):
      label        -- "Positive" / "Negative" / "Neutral" if a rule
                       fired confidently, else None (let the CNN decide).
      cleaned_text -- translated + cleaned text, ready for the CNN's
                       tokenizer, regardless of whether label is None.
    """
    emoji_verdict = pure_emoji_sentiment(raw_review)
    if emoji_verdict is not None:
        return emoji_verdict, clean_text(raw_review)

    translated = translate_to_english(raw_review)
    translated = normalize_smart_punctuation(translated)
    translated = expand_hashtags(translated)

    cleaned = clean_text(translated)
    dominant = dominant_text(translated)
    dominant_no_emoji = _strip_emoji(dominant)

    # Idioms are checked against the untouched `translated` text first:
    # dominant_text() can strip away the clause containing the idiom
    # (e.g. "Nothing special, but they don't disappoint either" drops
    # "Nothing special" because of the "but"). Falling back to
    # `dominant` still covers the cases that need it.
    idiom = idiom_override(translated) or idiom_override(dominant)
    if idiom is not None:
        return idiom, cleaned

    negated = negated_adjective_override(translated) or negated_adjective_override(dominant)
    if negated is not None:
        # "The design is not good BUT the garment is soft and comfortable":
        # the negation lives in the pre-"but" clause while the dominant
        # (post-"but") clause points the other way -> genuinely mixed.
        if contrast_clause_count(translated) >= 1:
            dominant_label = (
                negated_adjective_override(dominant)
                or vader_paragraph_override(dominant_no_emoji)
            )
            if dominant_label in ("Positive", "Negative") and dominant_label != negated:
                return "Neutral", cleaned
        return negated, cleaned

    hedge = hedge_override(dominant_no_emoji)
    if hedge is not None:
        return hedge, cleaned

    contrast_count = contrast_clause_count(translated)
    negative_contrast_count, negative_contrast_min_score = contrastive_negative_clause_count(translated)

    multi_contrast_fires = negative_contrast_count >= MULTI_CONTRAST_THRESHOLD
    single_strong_contrast_fires = (
        negative_contrast_count >= 1
        and negative_contrast_min_score is not None
        and negative_contrast_min_score <= _CONTRAST_CLAUSE_STRONG_NEG_BAND
    )

    # Only treat a flagged negative contrast clause as a genuine MIXED
    # review if the rest of the text still has positive content to
    # balance against -- otherwise a uniformly negative review gets
    # misread as "mixed" just for containing the word "but".
    has_positive_counterevidence = any(
        _vader.polarity_scores(s)["compound"] > _POSITIVE_COUNTEREVIDENCE_BAND
        for s in _split_sentences(dominant_no_emoji)
    )

    if (multi_contrast_fires or single_strong_contrast_fires) and has_positive_counterevidence:
        return "Neutral", cleaned

    if contrast_count <= 1:
        if has_mixed_sentiment(dominant_no_emoji):
            return "Neutral", cleaned

        override = vader_paragraph_override(dominant_no_emoji)
        if override is not None:
            return override, cleaned

    if cleaned.strip() == "":
        return "Neutral", cleaned

    return None, cleaned


# A compound of +0.11 is a weak/ambiguous signal, not a Positive verdict.
FALLBACK_POS_THRESHOLD = 0.25
FALLBACK_NEG_THRESHOLD = -0.25


def fallback_sentiment(text: str):
    """Classify text without TensorFlow for low-memory deployments."""
    compound = _vader.polarity_scores(text)["compound"]
    if compound >= FALLBACK_POS_THRESHOLD:
        label = "Positive"
    elif compound <= FALLBACK_NEG_THRESHOLD:
        label = "Negative"
    else:
        label = "Neutral"

    strength = min(abs(compound), 1.0)
    confidence = strength if label != "Neutral" else 1.0 - strength
    probabilities = {
        "Positive": 0.0,
        "Neutral": 0.0,
        "Negative": 0.0,
    }
    probabilities[label] = confidence
    remaining = 1.0 - confidence
    other_labels = [name for name in probabilities if name != label]
    for name in other_labels:
        probabilities[name] = remaining / len(other_labels)
    return label, confidence, probabilities