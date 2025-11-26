from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from tradingapi.core.exceptions import BusinessException, ValidationException
from tradingapi.models import StockBasicInfo
from tradingapi.repositories.stock_basic_info import StockBasicInfoRepository
from tradingapi.schemas.stocks import StockBasicInfoFilter, StockBasicInfoSchema
from tradingapi.services.base import BaseService


class StocksService(BaseService[StockBasicInfo, StockBasicInfoRepository]):
    """股票服务类 - 优化异步实现和错误处理"""
    
    repository_class = StockBasicInfoRepository
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        # Legacy compatibility - keep repo attribute
        self.repo = self.repository

    async def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[StockBasicInfoSchema]:
        """获取所有股票列表 - 增强分页和错误处理"""
        try:
            # SECURITY: Apply reasonable defaults and limits
            if limit is None:
                limit = 1000  # Default limit
            if limit > 5000:
                logger.warning(f"Large stock list requested: {limit}, capping at 5000")
                limit = 5000
                
            objs = await self.repository.get_all(limit=limit, offset=offset)
            
            # OPTIMIZATION: Batch validate schemas
            schemas = []
            for obj in objs:
                try:
                    schema = StockBasicInfoSchema.model_validate(obj)
                    schemas.append(schema)
                except Exception as e:
                    logger.warning(f"Failed to validate stock schema for {getattr(obj, 'symbol', 'unknown')}: {e}")
                    continue
                    
            logger.debug(f"StocksService: Retrieved {len(schemas)} stock schemas")
            return schemas
            
        except SQLAlchemyError as e:
            logger.error(f"StocksService: Database error listing stocks: {e}")
            raise BusinessException(f"获取股票列表失败: {str(e)}")
        except Exception as e:
            logger.error(f"StocksService: Unexpected error listing stocks: {e}")
            raise

    async def filter_stock(
        self, filter: StockBasicInfoFilter
    ) -> List[StockBasicInfoSchema]:
        """过滤股票 - 增强参数验证和错误处理"""
        try:
            # SECURITY: Validate filter parameters
            if not filter:
                raise ValidationException("过滤条件不能为空")
                
            # OPTIMIZATION: Log filter parameters for debugging
            filter_params = {
                "exchanges": filter.exchange,
                "sections": filter.sections,
                "stock_types": filter.stock_type,
                "industries": filter.industries,
                "date_range": f"{filter.start_listing_date} to {filter.end_listing_date}",
                "market_cap_range": f"{filter.min_market_cap} to {filter.max_market_cap}"
            }
            logger.debug(f"StocksService: Filtering stocks with params: {filter_params}")
            
            # SECURITY: Validate market cap range
            if filter.min_market_cap is not None and filter.max_market_cap is not None:
                if filter.min_market_cap > filter.max_market_cap:
                    raise ValidationException("最小市值不能大于最大市值")
                    
            # SECURITY: Validate date range
            if filter.start_listing_date and filter.end_listing_date:
                if filter.start_listing_date > filter.end_listing_date:
                    raise ValidationException("开始日期不能晚于结束日期")
            
            objs = await self.repository.advanced_filter(
                exchanges=filter.exchange,
                sections=filter.sections,
                stock_types=filter.stock_type,
                industries=filter.industries,
                start_listing_date=filter.start_listing_date,
                end_listing_date=filter.end_listing_date,
                min_float_market_value=filter.min_market_cap,
                max_float_market_value=filter.max_market_cap,
            )
            
            # OPTIMIZATION: Batch validate schemas with error handling
            schemas = []
            for obj in objs:
                try:
                    schema = StockBasicInfoSchema.model_validate(obj)
                    schemas.append(schema)
                except Exception as e:
                    logger.warning(f"Failed to validate filtered stock schema for {getattr(obj, 'symbol', 'unknown')}: {e}")
                    continue
                    
            logger.info(f"StocksService: Filtered {len(schemas)} stocks from {len(objs)} results")
            return schemas
            
        except ValidationException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"StocksService: Database error filtering stocks: {e}")
            raise BusinessException(f"股票过滤失败: {str(e)}")
        except Exception as e:
            logger.error(f"StocksService: Unexpected error filtering stocks: {e}")
            raise

    async def get_filter_options(self) -> Dict[str, List[str]]:
        """获取过滤选项 - 增强缓存和错误处理"""
        try:
            logger.debug("StocksService: Getting filter options")
            
            options = await self.repository.get_filter_options()
            
            # SECURITY: Validate and sanitize options
            if not isinstance(options, dict):
                logger.error("StocksService: Invalid filter options format")
                raise BusinessException("过滤选项格式错误")
                
            # OPTIMIZATION: Log option counts for monitoring
            option_counts = {key: len(values) if isinstance(values, list) else 0 
                           for key, values in options.items()}
            logger.debug(f"StocksService: Retrieved filter options: {option_counts}")
            
            return options
            
        except SQLAlchemyError as e:
            logger.error(f"StocksService: Database error getting filter options: {e}")
            raise BusinessException(f"获取过滤选项失败: {str(e)}")
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"StocksService: Unexpected error getting filter options: {e}")
            raise

    async def get_stock_name_by_code(self, code: str) -> Optional[str]:
        """根据股票代码获取股票名称 - 增强参数验证和错误处理"""
        try:
            # SECURITY: Validate input parameters
            if not code or not isinstance(code, str):
                raise ValidationException("股票代码不能为空且必须为字符串")
                
            code = code.strip().upper()  # Normalize code format
            if not code:
                raise ValidationException("股票代码不能为空")
                
            logger.debug(f"StocksService: Getting stock name for code: {code}")
            
            name = await self.repository.get_stock_name_by_symbol(code)
            
            if name:
                logger.debug(f"StocksService: Found stock name '{name}' for code {code}")
            else:
                logger.warning(f"StocksService: No stock found for code {code}")
                
            return name
            
        except ValidationException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"StocksService: Database error getting stock name for {code}: {e}")
            raise BusinessException(f"获取股票名称失败: {str(e)}")
        except Exception as e:
            logger.error(f"StocksService: Unexpected error getting stock name for {code}: {e}")
            raise

    async def get_stock_by_code(self, symbol: str) -> Optional[StockBasicInfo]:
        """根据股票代码获取股票信息 - 增强参数验证和错误处理"""
        try:
            # SECURITY: Validate input parameters
            if not symbol or not isinstance(symbol, str):
                raise ValidationException("股票代码不能为空且必须为字符串")
                
            symbol = symbol.strip().upper()  # Normalize symbol format
            if not symbol:
                raise ValidationException("股票代码不能为空")
                
            logger.debug(f"StocksService: Getting stock info for symbol: {symbol}")
            
            stock = await self.repository.get_stock_by_symbol(symbol)
            
            if stock:
                logger.debug(f"StocksService: Found stock info for symbol {symbol}")
            else:
                logger.warning(f"StocksService: No stock found for symbol {symbol}")
                
            return stock
            
        except ValidationException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"StocksService: Database error getting stock for {symbol}: {e}")
            raise BusinessException(f"获取股票信息失败: {str(e)}")
        except Exception as e:
            logger.error(f"StocksService: Unexpected error getting stock for {symbol}: {e}")
            raise