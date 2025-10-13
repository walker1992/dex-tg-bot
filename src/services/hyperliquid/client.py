"""
Hyperliquid exchange client implementation
"""
import asyncio
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    from hyperliquid.utils.signing import Account as HyperliquidAccount
    from eth_account import Account
    HYPERLIQUID_AVAILABLE = True
except ImportError as e:
    Info = None
    Exchange = None
    HyperliquidAccount = None
    Account = None
    HYPERLIQUID_AVAILABLE = False
    logger.warning(f"Hyperliquid SDK not available: {e}")

from ..base import (
    ExchangeService, Balance, Position, Order, Ticker, OrderBook, 
    FundingRate, SymbolInfo, OrderSide, OrderType, OrderStatus, 
    TimeInForce, ExchangeError, AuthenticationError, InvalidSymbolError
)


logger = logging.getLogger(__name__)


class HyperliquidClient(ExchangeService):
    """Hyperliquid exchange client"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_address = config.get("account_address")
        self.secret_key = config.get("secret_key")
        self.base_url = config.get("base_url", "https://api.hyperliquid.xyz")
        self.testnet = config.get("testnet", False)
        
        self.info: Optional[Info] = None
        self.exchange: Optional[Exchange] = None
        self.wallet: Optional[Any] = None
        
        # Rate limiting
        self.rate_limit = config.get("rate_limit", {})
        self.requests_per_minute = self.rate_limit.get("requests_per_minute", 60)
        self.burst_limit = self.rate_limit.get("burst_limit", 10)
        
    async def connect(self) -> bool:
        """Connect to Hyperliquid"""
        try:
            if not HYPERLIQUID_AVAILABLE:
                raise ExchangeError("Hyperliquid SDK not installed")
            
            # Initialize wallet
            if self.secret_key.startswith("0x"):
                self.wallet = Account.from_key(self.secret_key)
            else:
                self.wallet = HyperliquidAccount.from_key(self.secret_key)
            
            # Initialize Info client
            self.info = Info(self.base_url)
            
            # Initialize Exchange client
            self.exchange = Exchange(self.wallet, self.base_url)
            
            # Verify connection by getting account info
            await self.get_account_info()
            
            self.is_connected = True
            logger.info("Connected to Hyperliquid successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Hyperliquid: {e}")
            raise AuthenticationError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Hyperliquid"""
        self.is_connected = False
        self.info = None
        self.exchange = None
        self.wallet = None
        logger.info("Disconnected from Hyperliquid")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if not self.info or not self.account_address:
            raise ExchangeError("Not connected or missing account address")
        
        try:
            user_state = self.info.user_state(self.account_address)
            return {
                "account_address": self.account_address,
                "total_collateral": user_state.get("totalCollateral", 0),
                "total_margin_used": user_state.get("totalMarginUsed", 0),
                "total_ntl_pos": user_state.get("totalNtlPos", 0),
                "total_raw_usd": user_state.get("totalRawUsd", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise ExchangeError(f"Failed to get account info: {e}")
    
    async def get_balances(self) -> List[Balance]:
        """Get account balances (full balance including positions for futures)"""
        if not self.info or not self.account_address:
            raise ExchangeError("Not connected or missing account address")
        
        try:
            user_state = self.info.user_state(self.account_address)
            balances = []
            
            # Get wallet balances (not just positions)
            margin_summary = user_state.get("marginSummary", {})
            account_value = Decimal(str(margin_summary.get("accountValue", 0)))
            total_margin_used = Decimal(str(margin_summary.get("totalMarginUsed", 0)))
            total_ntl_pos = Decimal(str(margin_summary.get("totalNtlPos", 0)))
            
            # Add USDC balance (main wallet balance)
            if account_value > 0:
                free_usdc = account_value - total_margin_used
                balances.append(Balance(
                    asset="USDC",
                    free=free_usdc,
                    locked=total_margin_used,
                    total=account_value
                ))
            
            # Add position balances
            for asset in user_state.get("assetPositions", []):
                asset_name = asset.get("position", {}).get("coin", "")
                total = Decimal(str(asset.get("position", {}).get("szi", 0)))
                entry_px = Decimal(str(asset.get("position", {}).get("entryPx", 0)))
                
                # Calculate locked (margin used)
                locked = Decimal(str(asset.get("position", {}).get("marginUsed", 0)))
                free = total - locked
                
                # Only add if there's a position
                if total != 0:
                    balances.append(Balance(
                        asset=asset_name,
                        free=free,
                        locked=locked,
                        total=total
                    ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            raise ExchangeError(f"Failed to get balances: {e}")
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        if not self.info or not self.account_address:
            raise ExchangeError("Not connected or missing account address")
        
        try:
            user_state = self.info.user_state(self.account_address)
            positions = []
            
            for asset in user_state.get("assetPositions", []):
                position_data = asset.get("position", {})
                coin = position_data.get("coin", "")
                szi = Decimal(str(position_data.get("szi", 0)))
                
                if szi == 0:  # Skip zero positions
                    continue
                
                entry_px = Decimal(str(position_data.get("entryPx", 0)))
                unrealized_pnl = Decimal(str(position_data.get("unrealizedPnl", 0)))
                margin_used = Decimal(str(position_data.get("marginUsed", 0)))
                
                # Debug logging for raw position data
                logger.info(f"Hyperliquid raw position data for {coin}: {position_data}")
                logger.info(f"Hyperliquid asset data for {coin}: {asset}")
                
                # Determine side
                side = "LONG" if szi > 0 else "SHORT"
                
                # Get mark price
                mark_px = await self._get_mark_price(coin)
                
                # Calculate percentage
                percentage = (unrealized_pnl / (abs(szi) * entry_px)) * 100 if entry_px > 0 else Decimal(0)
                
                # Get leverage from position data (based on Hyperliquid SDK example)
                leverage = 1  # Default
                
                # According to the Hyperliquid SDK example, leverage is in position_data["leverage"]
                if "leverage" in position_data:
                    leverage_value = position_data.get("leverage")
                    logger.info(f"Raw leverage value for {coin}: {leverage_value} (type: {type(leverage_value)})")
                    
                    if leverage_value is not None:
                        # Handle different possible formats
                        if isinstance(leverage_value, (int, float)):
                            leverage = int(leverage_value)
                        elif isinstance(leverage_value, str):
                            try:
                                leverage = int(float(leverage_value))
                            except (ValueError, TypeError):
                                leverage = 1
                        elif isinstance(leverage_value, dict):
                            # If leverage is a dict, try to extract a numeric value
                            # Common keys might be "value", "leverage", "amount", "size", "cross", "isolated", etc.
                            for key in ["value", "leverage", "amount", "size", "cross", "isolated"]:
                                if key in leverage_value:
                                    try:
                                        leverage = int(float(leverage_value[key]))
                                        break
                                    except (ValueError, TypeError):
                                        continue
                            else:
                                # If no numeric value found, try to get the first numeric value
                                for key, value in leverage_value.items():
                                    try:
                                        leverage = int(float(value))
                                        break
                                    except (ValueError, TypeError):
                                        continue
                                else:
                                    leverage = 1
                        else:
                            leverage = 1
                    else:
                        leverage = 1
                else:
                    # Fallback: calculate leverage from position size and margin
                    position_value = abs(szi) * mark_px if mark_px > 0 else abs(szi) * entry_px
                    if margin_used > 0:
                        calculated_leverage = int(position_value / margin_used)
                        # Ensure leverage is at least 1 and reasonable
                        leverage = max(1, min(calculated_leverage, 100))
                    else:
                        leverage = 1  # Default to 1x if we can't calculate
                
                # Debug logging for leverage calculation
                position_value = abs(szi) * mark_px if mark_px > 0 else abs(szi) * entry_px
                leverage_from_api = position_data.get("leverage", "Not found")
                logger.info(f"Hyperliquid leverage debug - Symbol: {coin}, LeverageFromAPI: {leverage_from_api}, "
                           f"PositionValue: {position_value}, MarginUsed: {margin_used}, FinalLeverage: {leverage}")
                
                positions.append(Position(
                    symbol=coin,
                    side=side,
                    size=abs(szi),
                    entry_price=entry_px,
                    mark_price=mark_px,
                    pnl=unrealized_pnl,
                    percentage=percentage,
                    margin=margin_used,
                    leverage=leverage
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise ExchangeError(f"Failed to get positions: {e}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        if not self.info or not self.account_address:
            raise ExchangeError("Not connected or missing account address")
        
        try:
            open_orders = self.info.frontend_open_orders(self.account_address)
            orders = []
            
            for order_data in open_orders:
                order_symbol = order_data.get("coin", "")
                
                # Filter by symbol if specified
                if symbol and order_symbol != symbol:
                    continue
                
                order_id = str(order_data.get("oid", 0))
                is_buy = order_data.get("isBuy", False)
                sz = Decimal(str(order_data.get("sz", 0)))
                limit_px = Decimal(str(order_data.get("limitPx", 0)))
                
                # Map order status
                status_map = {
                    "open": OrderStatus.NEW,
                    "filled": OrderStatus.FILLED,
                    "canceled": OrderStatus.CANCELED
                }
                status = status_map.get(order_data.get("status", "open"), OrderStatus.NEW)
                
                orders.append(Order(
                    order_id=order_id,
                    symbol=order_symbol,
                    side=OrderSide.BUY if is_buy else OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    quantity=sz,
                    price=limit_px,
                    status=status,
                    filled_qty=Decimal(0),  # Hyperliquid doesn't provide filled quantity in open orders
                    avg_price=None,
                    time_in_force=TimeInForce.GTC,
                    created_at=order_data.get("timestamp", 0),
                    updated_at=order_data.get("timestamp", 0)
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise ExchangeError(f"Failed to get open orders: {e}")
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """Get specific order"""
        open_orders = await self.get_open_orders(symbol)
        
        for order in open_orders:
            if order.order_id == order_id:
                return order
        
        raise ExchangeError(f"Order {order_id} not found")
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        client_order_id: Optional[str] = None
    ) -> Order:
        """Place a new order"""
        if not self.exchange:
            raise ExchangeError("Not connected")
        
        try:
            is_buy = side == OrderSide.BUY
            
            # Map order type
            if order_type == OrderType.MARKET:
                order_type_dict = {"market": {}}
            elif order_type == OrderType.LIMIT:
                if not price:
                    raise ExchangeError("Price required for limit orders")
                order_type_dict = {
                    "limit": {
                        "tif": time_in_force.value
                    }
                }
            else:
                raise ExchangeError(f"Unsupported order type: {order_type}")
            
            # Place order
            result = self.exchange.order(
                symbol,
                is_buy,
                float(quantity),
                float(price) if price else 0,
                order_type_dict
            )
            
            # Create order object from result
            order_id = str(result.get("oid", 0))
            
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.NEW,
                filled_qty=Decimal(0),
                avg_price=None,
                time_in_force=time_in_force,
                created_at=int(asyncio.get_event_loop().time() * 1000),
                updated_at=int(asyncio.get_event_loop().time() * 1000),
                client_order_id=client_order_id
            )
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise ExchangeError(f"Failed to place order: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        if not self.exchange:
            raise ExchangeError("Not connected")
        
        try:
            result = self.exchange.cancel(symbol, int(order_id))
            return result.get("status") == "ok"
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise ExchangeError(f"Failed to cancel order: {e}")
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """Cancel all orders"""
        try:
            open_orders = await self.get_open_orders(symbol)
            
            for order in open_orders:
                await self.cancel_order(order.order_id, order.symbol)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise ExchangeError(f"Failed to cancel all orders: {e}")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker information"""
        if not self.info:
            raise ExchangeError("Not connected")
        
        try:
            l2 = self.info.l2_snapshot(symbol)
            levels = l2.get("levels", [])
            
            if len(levels) < 2:
                raise ExchangeError(f"No ticker data for {symbol}")
            
            bids = levels[0]
            asks = levels[1]
            
            bid_price = Decimal(str(bids[0]["px"])) if bids else Decimal(0)
            ask_price = Decimal(str(asks[0]["px"])) if asks else Decimal(0)
            
            # Get 24h stats (only for perpetual contracts)
            # For spot pairs, use bid/ask average as last price
            mark_price = Decimal(0)
            volume = Decimal(0)
            
            # Check if this is a spot pair (contains "/")
            if "/" in symbol:
                # For spot pairs, use average of bid and ask as last price
                if bid_price > 0 and ask_price > 0:
                    mark_price = (bid_price + ask_price) / 2
                else:
                    mark_price = bid_price if bid_price > 0 else ask_price
            else:
                # For perpetual contracts, try to get mark price from meta
                try:
                    meta_ctx = self.info.meta_and_asset_ctxs()
                    asset_ctxs = meta_ctx[1] if len(meta_ctx) > 1 else []
                    universe = meta_ctx[0].get("universe", [])
                    
                    for meta, ctx in zip(universe, asset_ctxs):
                        if meta.get("name") == symbol:
                            mark_price = Decimal(str(ctx.get("markPx", 0)))
                            volume = Decimal(str(ctx.get("dayNtlVlm", 0)))
                            break
                except Exception:
                    # Fallback to bid/ask average for perpetuals too
                    if bid_price > 0 and ask_price > 0:
                        mark_price = (bid_price + ask_price) / 2
            
            return Ticker(
                symbol=symbol,
                bid_price=bid_price,
                ask_price=ask_price,
                last_price=mark_price,
                volume=volume,
                price_change=Decimal(0),  # Not available in Hyperliquid API
                price_change_percent=Decimal(0),  # Not available in Hyperliquid API
                high_price=Decimal(0),  # Not available in Hyperliquid API
                low_price=Decimal(0),  # Not available in Hyperliquid API
                timestamp=int(asyncio.get_event_loop().time() * 1000)
            )
            
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise ExchangeError(f"Failed to get ticker: {e}")
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> OrderBook:
        """Get order book"""
        if not self.info:
            raise ExchangeError("Not connected")
        
        try:
            l2 = self.info.l2_snapshot(symbol)
            levels = l2.get("levels", [])
            
            bids = []
            asks = []
            
            if len(levels) >= 2:
                # Process bids
                for bid in levels[0][:limit]:
                    bids.append([Decimal(str(bid["px"])), Decimal(str(bid["sz"]))])
                
                # Process asks
                for ask in levels[1][:limit]:
                    asks.append([Decimal(str(ask["px"])), Decimal(str(ask["sz"]))])
            
            return OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=int(asyncio.get_event_loop().time() * 1000)
            )
            
        except Exception as e:
            logger.error(f"Failed to get order book: {e}")
            raise ExchangeError(f"Failed to get order book: {e}")
    
    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """Get funding rate"""
        if not self.info:
            raise ExchangeError("Not connected")
        
        try:
            meta_ctx = self.info.meta_and_asset_ctxs()
            asset_ctxs = meta_ctx[1] if len(meta_ctx) > 1 else []
            universe = meta_ctx[0].get("universe", [])
            
            for meta, ctx in zip(universe, asset_ctxs):
                if meta.get("name") == symbol:
                    funding_rate = Decimal(str(ctx.get("funding", 0)))
                    funding_time = ctx.get("fundingTime", 0)
                    next_funding_time = funding_time + 8 * 3600  # 8 hours later
                    
                    return FundingRate(
                        symbol=symbol,
                        funding_rate=funding_rate,
                        funding_time=funding_time,
                        next_funding_time=next_funding_time
                    )
            
            raise ExchangeError(f"Symbol {symbol} not found")
            
        except Exception as e:
            logger.error(f"Failed to get funding rate: {e}")
            raise ExchangeError(f"Failed to get funding rate: {e}")
    
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Get symbol information"""
        if not self.info:
            raise ExchangeError("Not connected")
        
        try:
            # Get asset info
            asset = self.info.name_to_asset(symbol)
            sz_decimals = int(self.info.asset_to_sz_decimals[asset])
            
            # Get tick size from order book
            l2 = self.info.l2_snapshot(symbol)
            levels = l2.get("levels", [])
            
            tick_size = Decimal("0.01")  # Default
            if len(levels) >= 2:
                bids = levels[0]
                if len(bids) >= 2:
                    tick_size = abs(Decimal(str(bids[0]["px"])) - Decimal(str(bids[1]["px"])))
            
            # Determine base and quote assets
            # Handle both formats: BASE/USDC and BASEUSDC
            if "/" in symbol:
                # Format: BASE/USDC or BASE/USDT
                parts = symbol.split("/")
                if len(parts) == 2:
                    base_asset = parts[0]
                    quote_asset = parts[1]
                else:
                    base_asset = symbol
                    quote_asset = "USDC"
            elif symbol.endswith("USDC"):
                base_asset = symbol[:-4]
                quote_asset = "USDC"
            elif symbol.endswith("USDT"):
                base_asset = symbol[:-4]
                quote_asset = "USDT"
            else:
                base_asset = symbol
                quote_asset = "USDC"
            
            return SymbolInfo(
                symbol=symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                tick_size=tick_size,
                step_size=Decimal("0.001"),  # Default
                min_qty=Decimal("0.001"),
                min_notional=Decimal("1.0"),
                is_spot=False,  # Hyperliquid is primarily futures
                is_futures=True
            )
            
        except Exception as e:
            logger.error(f"Failed to get symbol info: {e}")
            raise ExchangeError(f"Failed to get symbol info: {e}")
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        if not self.info:
            raise ExchangeError("Not connected")
        
        try:
            meta_ctx = self.info.meta_and_asset_ctxs()
            universe = meta_ctx[0].get("universe", [])
            
            symbols = []
            for meta in universe:
                symbols.append({
                    "symbol": meta.get("name", ""),
                    "base_asset": meta.get("name", "").replace("USDC", "").replace("USDT", ""),
                    "quote_asset": "USDC" if "USDC" in meta.get("name", "") else "USDT",
                    "status": "TRADING"
                })
            
            return {
                "timezone": "UTC",
                "server_time": int(asyncio.get_event_loop().time() * 1000),
                "symbols": symbols
            }
            
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise ExchangeError(f"Failed to get exchange info: {e}")
    
    async def _get_mark_price(self, symbol: str) -> Decimal:
        """Get mark price for symbol"""
        try:
            meta_ctx = self.info.meta_and_asset_ctxs()
            asset_ctxs = meta_ctx[1] if len(meta_ctx) > 1 else []
            universe = meta_ctx[0].get("universe", [])
            
            for meta, ctx in zip(universe, asset_ctxs):
                if meta.get("name") == symbol:
                    return Decimal(str(ctx.get("markPx", 0)))
            
            return Decimal(0)
            
        except Exception:
            return Decimal(0)
