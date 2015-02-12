// Daniel A. Noland
// Data Structures
// Lab #1 - shift cipher
// Generalized solution
// Fall 2014

// This is a "generalized" solution to the shift cipher problem.
// That is, the cipher specified in the assignment can be easily
// replaced with another cipher.
//
// Additionally, I show the method for reversing the cipher.
//
// NOTE: This is written against the c++11 standard, as per the
// professor's instructions.  Compile with the following command
// g++ -Wall -std=c++11 -o shift shift.cpp

#include <string>
#include <iostream>
#include <algorithm>
#include <locale>


typedef unsigned long long int AlphabetSizeType;
typedef char Char;

template <class T>
class AbstractCipherFunctional {

   protected:

      virtual T encipher(const T& clearData) = 0;

   public:

      virtual ~AbstractCipherFunctional() {}

      inline T operator ()(const T& clearData) {
         return encipher(clearData);
      }
};

template <class T>
struct ShiftCipherConfiguration {
   public:
      const T CIPHER_OFFSET;
      const T OFFSET_CODE;
      const AlphabetSizeType ALPHABET_SIZE;

      ShiftCipherConfiguration(
            T cipherOffset = T('j'),
            T offsetCode = T('a'),
            AlphabetSizeType alphabetSize = 26
      ) :
        CIPHER_OFFSET(cipherOffset - offsetCode),
        OFFSET_CODE(offsetCode),
        ALPHABET_SIZE(alphabetSize) {
           /* empty */
      }
};

template <class T>
class ShiftCipherFunctional : public AbstractCipherFunctional<T> {

   private:

      const ShiftCipherConfiguration<T>& _config;

   protected:



      // This is the line that does all the actual work
      T encipher(const T& clearData) {
         return (
               ( clearData - _config.OFFSET_CODE+ _config.CIPHER_OFFSET)
               % _config.ALPHABET_SIZE
               ) + _config.OFFSET_CODE;
      }


   public:

      ShiftCipherFunctional(
            const ShiftCipherConfiguration<T>& config
      ) :
      _config(config) {
      }

      ~ShiftCipherFunctional() {}

};

template <class Character = Char, template <class> class CipherFunctional = ShiftCipherFunctional >
class EncipheringStream {

   private:

      CipherFunctional<Character> _cipherFunctional;
      std::basic_string<Character> _cipherData;

   public:

      EncipheringStream(const std::basic_string<Character>& clearData, CipherFunctional<Character>& cipherFunctional)
         :
         _cipherFunctional(cipherFunctional)
         {
            _cipherData.resize(clearData.length());
            std::transform(
                  clearData.begin(),
                  clearData.end(),
                  _cipherData.begin(),
                  _cipherFunctional
            );
      }

      std::basic_string<Character> get_enciphered_data() const {
         return _cipherData;
      }

};

template <class Character = Char, template <class> class CipherFunctional = ShiftCipherFunctional >
inline std::ostream& operator<<(std::ostream& out, const EncipheringStream<Character, CipherFunctional>& estr) {
   return out << estr.get_enciphered_data();
}

template <class Character = Char, template <class> class CipherFunctional = ShiftCipherFunctional >
inline std::wostream& operator<<(std::wostream& out, const EncipheringStream<Character, CipherFunctional>& estr) {
   return out << estr.get_enciphered_data();
}

int main(int argc, char *argv[]) {
   std::basic_string<Char> clearData = "abcdefghijklmnopqrstuvwxyz";
   ShiftCipherConfiguration<Char> defaultConfig;
   ShiftCipherFunctional<Char> cipher(defaultConfig);
   EncipheringStream<Char> streamCipher(clearData, cipher);
   std::cout << streamCipher << std::endl;
   std::basic_string<Char> out = streamCipher.get_enciphered_data();
   char reverseCode =
         (defaultConfig.ALPHABET_SIZE + defaultConfig.CIPHER_OFFSET + 2*defaultConfig.OFFSET_CODE - 1)
         % defaultConfig.ALPHABET_SIZE;
   ShiftCipherConfiguration<Char> reverseConfig(reverseCode);
   ShiftCipherFunctional<Char> decipher(reverseConfig);
   EncipheringStream<Char> streamDecipher(out, decipher);
   std::cout << streamDecipher << std::endl;
   /* std::wcout.imbue(std::locale("en_US.UTF-8")); */
   /* std::locale::global(std::locale("en_US.UTF-8")); */
   /* std::ios_base::sync_with_stdio(false); */
   /* std::basic_string<Char> test = u8"OMG UNICODE! Ð Ñ Ò Ó Ô Õ Ö × Ø Ù"; */
   /* Char nTilde = 0x00D1; */
   /* ShiftCipherConfiguration<Char> largeAlphabetConfig(nTilde, 'a', 1 << (8*sizeof(Char))); */
   /* ShiftCipherFunctional<Char> largeAlphabetCipher(largeAlphabetConfig); */
   /* EncipheringStream<Char> largeAlphabetStreamCipher(test, cipher); */
   /* std::wcout << largeAlphabetStreamCipher << std::endl; */
   return 0;
}
