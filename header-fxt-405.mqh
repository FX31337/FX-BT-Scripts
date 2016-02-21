//+------------------------------------------------------------------+ 
//|                                                                  | 
//+------------------------------------------------------------------+ 
struct TestHistoryHeader 
  { 
   int               version;            // 405 
   char              copyright[64];      // copyright 
   char              symbol[12]; 
   int               period; 
   int               model;              // for what modeling type was the ticks sequence generated 
   int               bars;               // amount of bars in history 
   time_t            fromdate;           // ticks generated from this date 
   time_t            todate;             // ticks generating stopped at this date 
   double            modelquality;       // modeling quality 
   //---- general parameters 
   char              currency[12];       // currency base 
   int               spread; 
   int               digits; 
   double            point; 
   int               lot_min;            // minimum lot size 
   int               lot_max;            // maximum lot size 
   int               lot_step; 
   int               stops_level;        // stops level value 
   int               gtc_pendings;       // instruction to close pending orders at the end of day 
   //---- profit calculation parameters 
   double            contract_size;      // contract size 
   double            tick_value;         // value of one tick 
   double            tick_size;          // size of one tick 
   int               profit_mode;        // profit calculation mode        { PROFIT_CALC_FOREX, PROFIT_CALC_CFD, PROFIT_CALC_FUTURES } 
   //---- swap calculation 
   int               swap_enable;        // enable swap 
   int               swap_type;          // type of swap                   { SWAP_BY_POINTS, SWAP_BY_DOLLARS, SWAP_BY_INTEREST } 
   double            swap_long; 
   double            swap_short;         // swap overnight value 
   int               swap_rollover3days; // three-days swap rollover 
   //---- margin calculation 
   int               leverage;           // leverage 
   int               free_margin_mode;   // free margin calculation mode   { MARGIN_DONT_USE, MARGIN_USE_ALL, MARGIN_USE_PROFIT, MARGIN_USE_LOSS } 
   int               margin_mode;        // margin calculation mode        { MARGIN_CALC_FOREX,MARGIN_CALC_CFD,MARGIN_CALC_FUTURES,MARGIN_CALC_CFDINDEX }; 
   int               margin_stopout;     // margin stopout level 
   int               margin_stopout_mode;// stop out check mode            { MARGIN_TYPE_PERCENT, MARGIN_TYPE_CURRENCY } 
   double            margin_initial;     // margin requirements 
   double            margin_maintenance; // margin maintenance requirements 
   double            margin_hedged;      // margin requirements for hedged positions 
   double            margin_divider;     // margin divider 
   char              margin_currency[12];// margin currency 
   //---- commission calculation 
   double            comm_base;          // basic commission 
   int               comm_type;          // basic commission type          { COMM_TYPE_MONEY, COMM_TYPE_PIPS, COMM_TYPE_PERCENT } 
   int               comm_lots;          // commission per lot or per deal { COMMISSION_PER_LOT, COMMISSION_PER_DEAL } 
   //---- for internal use 
   int               from_bar;           // fromdate bar number 
   int               to_bar;             // todate bar number 
   int               start_period[6];    // number of bar at which the smaller period modeling started 
   int               set_from;           // begin date from tester settings 
   int               set_to;             // end date from tester settings 
   //---- 
   int               freeze_level;       // order's freeze level in points 
   int               generating_errors;   
   //---- 
   int               reserved[60]; 
  };
