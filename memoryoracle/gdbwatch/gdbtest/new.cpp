struct MyStruct {
   int* a;
   int b;
};

struct MyOtherStruct {
   MyStruct* a;
   int b;
};

int main(int argc, char *argv[]) {
   int* a;
   int* b = new int[10];
   int c = 3;
   MyOtherStruct exx;
   exx.a = new MyStruct[10];
   exx.b = 2;
   exx.a[0] = MyStruct();
   exx.a[0].b = 3;
   exx.a[1].a = &c;
   a = exx.a[1].a;
   *a = 42;
   b = nullptr;
   delete[] exx.a;
   return 0;
}
