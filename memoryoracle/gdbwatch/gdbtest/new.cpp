#include <string>

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
   return a + 2;
}

int main(int argc, char *argv[]) {
   /* int* a; */
   /* int* b = new int[10]; */
   /* int c = 3; */
   int a[5] = { 1, 2, 3, 4, 5 };
   float b[2][2] = { {1 ,2.17}, {3.14, 4} };
   double* c = new double[10];
   std::string h = "hello, world";
   MyOtherStruct exx;
   exx.a = new MyStruct[5];
   exx.b = 2;
   exx.a[0] = MyStruct();
   exx.a[0].b = 3;
   exx.a[0].b = func(4);
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
