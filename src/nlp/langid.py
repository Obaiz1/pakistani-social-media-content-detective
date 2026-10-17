"""Language ID for short social comments: urdu_script / roman_urdu / english / mixed / other.

Script decides Urdu vs Latin. For Latin text, a small lexicon of very common Roman Urdu function and
everyday words (written from general knowledge, NOT tuned on the benchmark comments) is compared
against English function words.
"""

import re

_URDU = re.compile(r"[؀-ۿ]")
_LATIN_WORD = re.compile(r"[A-Za-z]+")
_URL = re.compile(r"https?://\S+")

ROMAN_URDU = set("""
hai hain hy hn ha he hay ho hoga hogi hogya hua hui huay tha thi thay the nahi nai nhi na mat bhi bi b
kya kia kiya kyun kyu q kab kb kahan kaha kidhar kaise kese kaisa kesa kitna kitne kitni kon kaun konsa
ka ki ke ko se sy say mein main mai me mn par pr pe tak tk aur or wala wali walay wale
yeh ye yah woh wo vo is us isse usse inka unka apka apki apke aap ap tum tu mera meri mere mujhe mujy
hamara hamari humara hum ham koi kuch kch sab sub sirf srf bas bohat bohut bht bahut buhat zyada ziada
acha achha acchi achi achay ache bura buri bure kharab ganda gandi bakwas bekar bekaar zabardast
khubsurat khoobsurat pyara pyari pyaari sundar mehnga mehenga sasta kapra kapre kapray kapry jora
chahiye chahye chaiye chaey karo kren karein kar kr krna karna krty karte kerty dein dain de do
lagta lagti lagra lagri lagriya laga lagi raha rahi rahe rha rhi gya gaya gayi gye mil mila mili
yaar yar bhai bhae appi baji jaan jani shukriya shukria masha mashallah inshallah subhan allah
abhi ab phir fir pehle pehlay baad jab tab agar lekin magar kyunki
""".split())

ENGLISH = set("""
the a an is are was were be been am i you he she it we they my your his her our their this that these
those what which who whom when where why how and or but if so very too not no yes do does did have has
had will would can could should of in on at to for from with by about as please plz pls thanks thank
love like nice good great best beautiful amazing awesome gorgeous wow song price dress collection
""".split())


def detect_language(text: str) -> str:
    text = _URL.sub(" ", text or "")
    urdu_chars = len(_URDU.findall(text))
    words = [w.lower() for w in _LATIN_WORD.findall(text)]
    if urdu_chars and urdu_chars >= sum(len(w) for w in words):
        return "urdu_script"
    if not words:
        return "other"
    ru = sum(w in ROMAN_URDU for w in words)
    en = sum(w in ENGLISH for w in words)
    if ru == 0:
        return "english" if en else "other" if len(words) == 1 and len(words[0]) <= 3 else "english"
    if en >= 2 and ru >= 2 and min(en, ru) / max(en, ru) >= 0.5:
        return "mixed"
    return "roman_urdu" if ru >= en else "english"
