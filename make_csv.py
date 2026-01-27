import FinanceDataReader as fdr
print("데이터 가져오는 중...")
df = fdr.StockListing('KRX')
df.to_csv('krx_list.csv', index=False, encoding='utf-8-sig')
print("성공! krx_list.csv 파일이 생성되었습니다.")