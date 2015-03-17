#include <string>
#include <iostream>

struct MyStruct;
struct MyOtherStruct;

struct MyStruct {
   int* a;
   int b;
   MyOtherStruct* c;
};

struct MyOtherStruct {
   MyStruct* a;
   int b;
   MyOtherStruct* cc;
};

int func(int a) {
   if (a == 0 || a == 1) {
      return 1;
   }
   int b = func(a - 1);
   int c = func(a - 2);
   return a + b + c;
}

int punc(int a) {
   int b = 3;
   return b*a;
}

typedef unsigned long ulong;

int main(int argc, char *argv[]) {
   /* int* a; */
   /* int* b = new int[10]; */
   /* int c = 3; */
   int aa = 4;
   int a[5] = { 1, 2, 3, 4, 5 };
   float b[2][2] = { {1 ,2.17}, {3.14, 4} };
   float d[2][3][2] = { {1 ,2.17, 3.14}, {0, 4} };
   double* c = new double[10];
   std::string h = "hello, world";
   char* h2 = "goodbye, world";
   char* h3;
   char science = 'j';
   h3 = &science;
   MyOtherStruct exx;
   exx.a = new MyStruct[5];
   exx.b = 2;
   exx.a[0] = MyStruct();
   exx.a[0].b = 3;
   exx.a[0].b = func(aa);
   std::cout << exx.a[0].b << std::endl;
   exx.cc = &exx;
   exx.a[0].c = &exx;
   /* exx.a[1].a = &c; */
   /* a = exx.a[1].a; */
   /* *a = 42; */
   /* b = nullptr; */
   delete[] exx.a;
   delete[] c;
   return 0;
}
