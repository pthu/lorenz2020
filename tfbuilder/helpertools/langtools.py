# Languages.py contains several classes with methods that
# are important to process strings, both for TEI XML and CSV.
# Any information that is specific for the TEI XML 
# conversion, can be found in config.py
import pickle
from data import attrib_errors
from helpertools.unicodetricks import splitPunc, cleanWords, plainCaps, plainLow
from helpertools.data.greek import MOVEABLE_NU_ENDINGS, MOVEABLE_NU, ELISION, CRASIS, NOMINASACRA, BIBLICAL_BOOKS
#from cltk.corpus.greek.beta_to_unicode import Replacer
#import betacode.conv

from unicodedata import normalize
# from greek_normalisation.normalise import Normaliser

#beta_to_uni = Replacer()



class Generic:
    udnorm = 'NFD'

    @classmethod
    def replace(cls, token):
        """NB the replace method should always return a list or tuple in the original token format"""
        return (token,)
    
    @classmethod
    def ltNormalize(cls, string):
        """langtools normalize usually uses the unicodedata
        normalize() function; however, for many languages it
        will be overriden with a custom normalization function"""
        return normalize(cls.udnorm, string) 
    
    @classmethod
    def tokenize(cls, sentence, punc=False, clean=False,
                 splitters=None, non_splitters=('-',)):
        """This advanced tokenizer is based on the unicodedata
        categories. It is able to tokenize much more sophisticated
        than the python sentence.split() function.

        punc=False:
            All punctuation before and after a word is deleted.

        punc=True:
            All punctuation before and after a word is given

        clean=False:
            If punctuation stands in the middle of letters, 
            without surrounding spaces, the word is split 
            on punctuation.

        clean=True:
            If punctuation stands in the middle of a word,
            without spaces, the punctuation is deleted and the 
            two parts of the word are glued together.

        returns ['string', 'string', ...]
        """
        return cleanWords(sentence, norm=cls.udnorm, clean=clean,
                          splitters=splitters, non_splitters=non_splitters)
    
    @classmethod
    def splitTokenize(cls, sentence, punc=True, clean=False,
                      splitters=None, non_splitters=('-',)):
        """Tokenizes a sentence, while preserving punctuation.
        
        The difference with tokenize() is that splitTokenize
        preserves splits punctuation from the word.
        
        returns: ((pre, word, post), (pre, word, post), ...)
        """
        return splitPunc(sentence, norm=cls.udnorm, clean=clean,
                         splitters=splitters, non_splitters=non_splitters)

    # STANDARD TEXT OUTPUT FORMATS
    @classmethod
    def origWord(cls, token, split=True):
        """returns the original word according to the
        preferred unicode normalization as defined
        in tf_config.py
        
        returns 'normalized_string'
        """
        if split:
            return normalize(cls.udnorm, ''.join(token))
        else:
            return normalize(cls.udnorm, token)
    
    @classmethod
    def mainWord(cls, token, split=True, clean=True, splitters=None, non_splitters=('-',)):
        """returns the lowered original word,
        but stripped of punctuation
        before, inbetween and after with
        normalized accentuation
        """
        if split:
            pre, word, post = token
            return normalize(cls.udnorm, word.lower())
        else:
            return cleanWords(token, norm=cls.udnorm, clean=clean, split=split,
                              splitters=splitters, non_splitters=non_splitters).lower()
    
    @staticmethod
    def plainWord(token, split=True, caps=False):
        if split:
            pre, word, post = token
            if caps:
                return plainCaps(word)
            else:
                return plainLow(word)
        else:
            if caps:
                return plainCaps(token)
            else:
                return plainLow(token)
                      

class Greek(Generic):
    udnorm = 'NFD'
    ELISION_norm = {normalize('NFC', k): v for k, v in ELISION.items()}
    CRASIS_norm = {normalize('NFC', k): v for k, v in CRASIS.items()}
#     lemmatizer = startLemmatizer.__func__()
    
    @classmethod
    def replace(cls, token):
        pre, word, post = token
        
        # If betacode, convert to unicode TURNED OFF FOR LORENZ2020
#         try:
#             word.encode('ascii')
#             word = normalize(cls.udnorm, betacode.conv.beta_to_uni(word))
#         except UnicodeEncodeError:
#             word = normalize(cls.udnorm, word)
        
        plain_word = plainLow(word)
        
        # Handling elided forms
        if normalize('NFC', word) in cls.ELISION_norm:
            repl_word = normalize(cls.udnorm, cls.ELISION_norm[normalize('NFC', word)])
        elif post.startswith(('᾿', '’', '᾽', "'", 'ʹ')):
            if normalize('NFC', word + '᾽') in cls.ELISION_norm:
                repl_word = normalize(cls.udnorm, cls.ELISION_norm[normalize('NFC', word + '᾽')])
            else:
                repl_word = word
        elif word.endswith(('᾿', '’', '᾽', "'", 'ʹ')):
            if normalize('NFC', word[:-1] + '᾽') in cls.ELISION_norm:
                repl_word = normalize(cls.udnorm, cls.ELISION_norm[normalize('NFC', word[:-1] + '᾽')])
            else:
                repl_word = word
        # Handling crasis forms
        elif normalize('NFC', word) in cls.CRASIS_norm:
            repl_word = normalize(cls.udnorm, cls.CRASIS_norm[normalize('NFC', word)])
        # Deletion of movable-nu
        elif plain_word in MOVEABLE_NU:
            repl_word = word[:-1]
        # Next is unreliable!
#         elif plain_word[-3:] in MOVEABLE_NU_ENDINGS and len(plain_word) > 3:
#             repl_word = word[:-1]
        # Handling final-sigma
        elif plain_word.endswith('σ'):
            repl_word = word[:-1] + 'ς'
        # Handling various forms of ου
        elif plain_word in ('ουχ', 'ουκ'):
            repl_word = word[:-1]
        # Handling ἐξ
        elif plain_word == 'εξ':
            repl_word = word[:-1] + 'κ'
        # Handling nomina sacra
        elif plain_word in NOMINASACRA:
            repl_word = NOMINASACRA[plain_word]
        else:
            repl_word = word
        
        if len(repl_word.split(' ')) > 1:
            repl_word_split = list(enumerate(repl_word.split(' '), start=1))
            pre_assigned = False
            result = []
            for n, w in repl_word_split:
                if not pre_assigned:
                    result.append(tuple((pre, w, ' ')))
                    pre_assigned = True
                elif n == len(repl_word_split):
                    result.append(tuple(('', w, post)))
                else:
                    result.append(tuple(('', w, ' ')))
            return tuple(result)
        else:
            return ((pre, repl_word, post),)

        #TURNED OFF BECAUSE OF LORENZ2020
#     @classmethod
#     def jtNormalize(cls, token):
#         """This method returns a normalized word
#         according to the normalization procedure
#         of James Tauber; formatted in the NFD format.
#         """
#         pre, word, post = token
#         return normalize(cls.udnorm, Normaliser().normalise(word)[0])
        
    @staticmethod
    def startLemmatizer():
        """The lemmatizer contains only NFD formatted data
        """
        lemmatizer = {0:0} # dummy FOR LORENZ2020
#         print('    |  loading lemmatizer...')
#         print('    |  ...')
#         lemmatizer_open = open('data/lemmatizer.pickle', 'rb')
#         lemmatizer = pickle.load(lemmatizer_open)
#         lemmatizer_open.close()
        return lemmatizer

    # Start the lemmatizer immediately to be used in the lemmatize() method
    lemmatizer = startLemmatizer.__func__()
    
    @classmethod
    def lemmatize(cls, word):
        word = normalize('NFD', word.lower())
        if word in cls.lemmatizer:
            lemma = normalize(cls.udnorm, ','.join(cls.lemmatizer[word]))
        else:
            # TURNED OFF BECAUSE OF LORENZ2020
            # word = cls.jtNormalize(('', word, ''))
            if word in cls.lemmatizer:
                lemma = normalize(cls.udnorm, ','.join(cls.lemmatizer[word]))
            else:
                word = cls.plainWord(('', word, ''))
                if word in cls.lemmatizer:
                    lemma = normalize(cls.udnorm, ','.join(cls.lemmatizer[word]))
                else:
                    lemma = f'*{normalize(cls.udnorm, word)}'
        return lemma

    @staticmethod
    def checkEncoding(elem):
        try:
            elem.encode('ascii')
            return 'beta'
        except UnicodeEncodeError:
            return 'uni'
    
    # TURNED OFF BECAUSE OF LORENZ2020
#     @classmethod
#     def beta2uni(cls, word):
#         """Converts betacode to unicode"""
# #         beta_to_uni = Replacer()
#         return normalize(cls.udnorm, beta_to_uni.beta_code(word))
    
#     @classmethod
#     def uni2betaPlain(cls, word):
#         """Converts unicode to unaccented betacode,
#         to be used in the Morpheus morphological
#         analyser
#         """
#         word_plain = plainLow(word)
#         return betacode.conv.uni_to_beta(word_plain)
                      
    @staticmethod
    def morphology(plain_betacode_word):
        pass
    
    # ADDITIONAL TEXT OUTPUT FORMATS
    #TURNED OFF BECAUSE OF LORENZ2020
#     @classmethod
#     def normWord(cls, token, split=True):
#         if split:
#             return normalize(cls.udnorm, cls.jtNormalize(token))
#         else:
#             return normalize(cls.udnorm, cls.jtNormalize(('', token, '')))

        # TURNED OFF BECAUSE OF LORENZ2020
#     @classmethod
#     def betaPlainWord(cls, token, split=True):
#         if split:
#             pre, word, post = token
#             return cls.uni2betaPlain(word)
#         else:
#             return cls.uni2betaPlain(token)
    
    @classmethod
    def lemmaWord(cls, token, split=True):
        if split:
            pre, word, post = token
            return cls.lemmatize(word)
        else:
            return cls.lemmatize(token)
                      
class Latin(Generic):
    udnorm = 'NFD'
    
#     @staticmethod
#     def tokenize(self, string):
        
#     @staticmethod
#     def normalize(self):
        
#     @staticmethod
#     def lemmatize(self, word):
    
  
