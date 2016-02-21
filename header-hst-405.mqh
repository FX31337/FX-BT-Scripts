#pragma pack(push,1) 
struct TestHistory 
  { 
   time_t            otm;                // bar time 
   double            open;               // OHLCV values 
   double            low; 
   double            high; 
   double            close; 
   double            volume; 
   time_t            ctm;                // the current time within a bar 
   int               flag;               // flag to launch an expert (0 - bar will be modified, but the expert will not be launched) 
  }; 
#pragma pack(pop)
